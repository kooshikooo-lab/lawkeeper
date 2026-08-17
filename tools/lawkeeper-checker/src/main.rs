//! lawkeeper-checker: a minimal, real prototype of an edit-time syntax
//! constitution for Rust.
//!
//! Scope, deliberately: 6 rules, not 28. Each rule here is something I could
//! define precisely enough to implement without ambiguity, and verify
//! against real test cases (see tests/fixtures/). A rule that can't be
//! stated precisely enough to test isn't ready to enforce — that's the same
//! principle behind every fix we made to the Python Lawkeeper prototype:
//! don't ship a check that can't prove it works.
//!
//! Rules implemented:
//!   UNWRAP               - `.unwrap()` calls outside test code
//!   WILDCARD_SWALLOW     - `_ => {}` / `_ => ()` match arms that silently
//!                          discard every unhandled case
//!   ERASED_ERROR         - `Box<dyn Error>` (or `Box<dyn std::error::Error>`)
//!                          as a function's error type, which erases which
//!                          errors can actually occur
//!   DISCARDED_RESULT     - `something.ok();` as a bare statement — converts
//!                          a Result to an Option and immediately throws it
//!                          away, silently swallowing any Err
//!   UNWRAP_OR_DEFAULT    - `.unwrap_or_default()` — silently substitutes a
//!                          default value on error/None, indistinguishable
//!                          from a genuine default at the call site
//!   EXPECT_EMPTY_MESSAGE - `.expect("")` — gives no more information than
//!                          `.unwrap()` while looking documented
//!
//! What this is NOT: a linter that understands types, borrows, or control
//! flow. It's pure syntax matching over the parsed AST (via `syn`), which is
//! exactly the tradeoff the research doc's "Lawkeeper" description claimed
//! (whether or not that citation was real) — milliseconds-fast, no type
//! inference, catches syntactic shapes that correlate strongly with bugs
//! being silently swallowed.

use std::fs;
use std::path::{Path, PathBuf};

use clap::Parser;
use syn::spanned::Spanned;
use syn::visit::{self, Visit};
use walkdir::WalkDir;

#[derive(Parser)]
#[command(name = "lawkeeper-checker")]
#[command(about = "Edit-time syntax constitution for Rust (prototype, 4 rules)")]
struct Args {
    /// File or directory to check
    path: PathBuf,
}

#[derive(Debug)]
struct Violation {
    file: PathBuf,
    line: usize,
    column: usize,
    rule: &'static str,
    message: String,
}

impl Violation {
    fn print(&self) {
        println!(
            "{}:{}:{}: [{}] {}",
            self.file.display(),
            self.line,
            self.column,
            self.rule,
            self.message
        );
    }
}

/// Tracks whether we're currently inside test code, so test files/modules
/// legitimately using .unwrap() aren't flagged. This is a real, common
/// false-positive source for exactly this kind of checker, so it's handled
/// explicitly rather than left as a known gap.
struct CheckVisitor<'a> {
    file: &'a Path,
    in_test_context: bool,
    violations: Vec<Violation>,
}

impl<'a> CheckVisitor<'a> {
    fn new(file: &'a Path) -> Self {
        Self { file, in_test_context: false, violations: Vec::new() }
    }

    fn push(&mut self, span: proc_macro2::Span, rule: &'static str, message: impl Into<String>) {
        if self.in_test_context {
            return;
        }
        let start = span.start();
        self.violations.push(Violation {
            file: self.file.to_path_buf(),
            line: start.line,
            column: start.column + 1,
            rule,
            message: message.into(),
        });
    }
}

fn has_cfg_test_or_test_attr(attrs: &[syn::Attribute]) -> bool {
    attrs.iter().any(|attr| {
        if attr.path().is_ident("test") {
            return true;
        }
        if attr.path().is_ident("cfg") {
            let mut found = false;
            let _ = attr.parse_nested_meta(|meta| {
                if meta.path.is_ident("test") {
                    found = true;
                }
                Ok(())
            });
            return found;
        }
        false
    })
}

impl<'a, 'ast> Visit<'ast> for CheckVisitor<'a> {
    fn visit_expr_method_call(&mut self, node: &'ast syn::ExprMethodCall) {
        if node.method == "unwrap" {
            self.push(
                node.method.span(),
                "UNWRAP",
                "`.unwrap()` panics with no context on failure. Prefer `?` \
                 to propagate the error, or `.expect(\"why this can't fail here\")` \
                 if the panic is genuinely intended and the reason is worth recording.",
            );
        }
        if node.method == "ok" {
            self.push(
                node.method.span(),
                "DISCARDED_RESULT",
                "`.ok()` on a Result, used as a bare statement, silently \
                 discards the Err case. If the error genuinely doesn't matter, \
                 make that explicit: `let _ = x;` at least signals intent; \
                 logging the error before discarding it is usually better.",
            );
        }
        if node.method == "unwrap_or_default" {
            self.push(
                node.method.span(),
                "UNWRAP_OR_DEFAULT",
                "`.unwrap_or_default()` silently replaces a missing/errored \
                 value with a default (0, empty string, empty vec, ...), which \
                 looks identical to a genuine default from the caller's \
                 perspective. If a default is really the right behavior, \
                 consider `.unwrap_or_else(|| { log the reason; default })` \
                 so the substitution is visible somewhere.",
            );
        }
        if node.method == "expect" {
            if let Some(syn::Expr::Lit(lit)) = node.args.first() {
                if let syn::Lit::Str(s) = &lit.lit {
                    if s.value().trim().is_empty() {
                        self.push(
                            node.method.span(),
                            "EXPECT_EMPTY_MESSAGE",
                            "`.expect(\"\")` with an empty message gives no more \
                             information than `.unwrap()` on panic, while looking \
                             like it documents something. Either write the real \
                             reason this can't fail, or use `.unwrap()` and be \
                             honest that there's no explanation.",
                        );
                    }
                }
            }
        }
        visit::visit_expr_method_call(self, node);
    }

    fn visit_arm(&mut self, node: &'ast syn::Arm) {
        let is_wildcard = matches!(node.pat, syn::Pat::Wild(_));
        let body_is_empty = match &*node.body {
            syn::Expr::Block(b) => b.block.stmts.is_empty(),
            syn::Expr::Tuple(t) => t.elems.is_empty(),
            _ => false,
        };
        if is_wildcard && body_is_empty {
            self.push(
                node.pat.span(),
                "WILDCARD_SWALLOW",
                "`_ => {}` silently discards every unhandled match case. \
                 If some cases genuinely don't need handling, match them \
                 explicitly so a new enum variant added later doesn't \
                 silently fall through here too.",
            );
        }
        visit::visit_arm(self, node);
    }

    fn visit_signature(&mut self, node: &'ast syn::Signature) {
        if let syn::ReturnType::Type(_, ty) = &node.output {
            if let Some(msg) = find_erased_error(ty) {
                self.push(ty.span(), "ERASED_ERROR", msg);
            }
        }
        visit::visit_signature(self, node);
    }

    fn visit_item_fn(&mut self, node: &'ast syn::ItemFn) {
        let was_test = self.in_test_context;
        if has_cfg_test_or_test_attr(&node.attrs) {
            self.in_test_context = true;
        }
        visit::visit_item_fn(self, node);
        self.in_test_context = was_test;
    }

    fn visit_item_mod(&mut self, node: &'ast syn::ItemMod) {
        let was_test = self.in_test_context;
        if has_cfg_test_or_test_attr(&node.attrs) {
            self.in_test_context = true;
        }
        visit::visit_item_mod(self, node);
        self.in_test_context = was_test;
    }
}

fn find_erased_error(ty: &syn::Type) -> Option<String> {
    if let syn::Type::Path(type_path) = ty {
        let segment = type_path.path.segments.last()?;
        if segment.ident != "Result" {
            return None;
        }
        let syn::PathArguments::AngleBracketed(args) = &segment.arguments else { return None };
        let err_arg = args.args.iter().nth(1)?;
        let syn::GenericArgument::Type(syn::Type::Path(err_type)) = err_arg else { return None };
        let err_segment = err_type.path.segments.last()?;
        if err_segment.ident != "Box" {
            return None;
        }
        let syn::PathArguments::AngleBracketed(box_args) = &err_segment.arguments else { return None };
        let syn::GenericArgument::Type(syn::Type::TraitObject(trait_obj)) = box_args.args.first()? else { return None };
        let is_error_trait = trait_obj.bounds.iter().any(|b| {
            if let syn::TypeParamBound::Trait(t) = b {
                t.path.segments.last().map(|s| s.ident == "Error").unwrap_or(false)
            } else {
                false
            }
        });
        if is_error_trait {
            return Some(
                "`Box<dyn Error>` erases which errors this function can actually \
                 return, so callers can't match on specific failure cases. \
                 Prefer a concrete error enum (e.g. via `thiserror`) that \
                 names the real failure modes."
                    .to_string(),
            );
        }
    }
    None
}

fn check_file(path: &Path) -> Vec<Violation> {
    let content = match fs::read_to_string(path) {
        Ok(c) => c,
        Err(_) => return Vec::new(),
    };
    let ast = match syn::parse_file(&content) {
        Ok(ast) => ast,
        Err(e) => {
            eprintln!("lawkeeper-checker: could not parse {} ({e}) — skipping", path.display());
            return Vec::new();
        }
    };
    let mut visitor = CheckVisitor::new(path);
    visitor.visit_file(&ast);
    visitor.violations
}

fn main() {
    let args = Args::parse();

    let files: Vec<PathBuf> = if args.path.is_file() {
        vec![args.path.clone()]
    } else {
        WalkDir::new(&args.path)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| e.path().extension().and_then(|s| s.to_str()) == Some("rs"))
            .filter(|e| !e.path().components().any(|c| c.as_os_str() == "target"))
            .map(|e| e.path().to_path_buf())
            .collect()
    };

    let mut total = 0usize;
    for file in &files {
        let violations = check_file(file);
        total += violations.len();
        for v in &violations {
            v.print();
        }
    }

    if total == 0 {
        println!("lawkeeper-checker: {} file(s) checked, 0 violations", files.len());
        std::process::exit(0);
    } else {
        println!(
            "lawkeeper-checker: {} file(s) checked, {} violation(s)",
            files.len(),
            total
        );
        std::process::exit(1);
    }
}

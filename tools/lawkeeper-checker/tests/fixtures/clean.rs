use thiserror::Error;

#[derive(Debug, Error)]
enum ConfigError {
    #[error("port could not be parsed: {0}")]
    BadPort(#[from] std::num::ParseIntError),
    #[error("io failure: {0}")]
    Io(#[from] std::io::Error),
}

// Clean equivalent of the UNWRAP violation: propagate with `?`.
fn parse_port(s: &str) -> Result<u16, ConfigError> {
    Ok(s.parse::<u16>()?)
}

// Clean equivalent of DISCARDED_RESULT: log the error instead of discarding it.
fn write_log(msg: &str) {
    if let Err(e) = std::fs::write("/tmp/log.txt", msg) {
        eprintln!("failed to write log: {e}");
    }
}

// Clean equivalent of WILDCARD_SWALLOW: handle every case explicitly.
enum Status {
    Ready,
    Pending,
    Failed(String),
}

fn handle_status(s: Status) {
    match s {
        Status::Ready => println!("ready"),
        Status::Pending => println!("pending"),
        Status::Failed(reason) => eprintln!("failed: {reason}"),
    }
}

// Clean equivalent of ERASED_ERROR: a concrete error type.
fn load_config() -> Result<String, ConfigError> {
    Ok("config".to_string())
}

// Clean equivalent of UNWRAP_OR_DEFAULT: log the fallback explicitly.
fn retry_count(s: &str) -> u32 {
    s.parse::<u32>().unwrap_or_else(|e| {
        eprintln!("invalid retry count '{s}': {e}, defaulting to 0");
        0
    })
}

// Clean equivalent of EXPECT_EMPTY_MESSAGE: a real, non-empty reason.
// A non-empty .expect() message should NOT be flagged.
fn parse_id(s: &str) -> u64 {
    s.parse::<u64>().expect("id is validated as numeric before this call")
}

// A non-empty wildcard arm should NOT be flagged — only empty ones are.
fn handle_status_with_default(s: Status) {
    match s {
        Status::Ready => println!("ready"),
        _ => println!("not ready"),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // .unwrap() in test code is fine and should NOT be flagged.
    #[test]
    fn test_parse_port() {
        assert_eq!(parse_port("8080").unwrap(), 8080);
    }
}

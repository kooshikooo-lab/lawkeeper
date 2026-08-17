use std::error::Error;

// Violation: UNWRAP
fn parse_port(s: &str) -> u16 {
    s.parse::<u16>().unwrap()
}

// Violation: DISCARDED_RESULT
fn write_log(msg: &str) {
    std::fs::write("/tmp/log.txt", msg).ok();
}

// Violation: WILDCARD_SWALLOW
enum Status {
    Ready,
    Pending,
    Failed(String),
}

fn handle_status(s: Status) {
    match s {
        Status::Ready => println!("ready"),
        _ => {}
    }
}

// Violation: ERASED_ERROR
fn load_config() -> Result<String, Box<dyn Error>> {
    Ok("config".to_string())
}

// Violation: UNWRAP_OR_DEFAULT
fn retry_count(s: &str) -> u32 {
    s.parse::<u32>().unwrap_or_default()
}

// Violation: EXPECT_EMPTY_MESSAGE
fn parse_id(s: &str) -> u64 {
    s.parse::<u64>().expect("")
}

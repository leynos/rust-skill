# Worked examples

Use these examples to tighten compiled scope before reaching for any lint
suppression.

## Example 1: Feature-gated import

Prefer putting the import and helper behind the same feature boundary.

### Avoid for feature-gated imports

```rust
use rustls::ClientConfig;

pub fn connect() {
    #[cfg(feature = "tls")]
    let _config = ClientConfig::builder();
}
```

In builds without `tls`, the import is still compiled into the module and
becomes unused.

### Prefer for feature-gated imports

```rust
#[cfg(feature = "tls")]
use rustls::ClientConfig;

pub fn connect() {
    #[cfg(feature = "tls")]
    let _config = ClientConfig::builder();
}
```

### Prefer even more when the dependency is truly local

```rust
pub fn connect() {
    #[cfg(feature = "tls")]
    {
        use rustls::ClientConfig;

        let _config = ClientConfig::builder();
    }
}
```

This keeps the module dependency picture accurate: `rustls` only appears where
the compiled path actually uses it.

## Example 2: Target-specific helper module

Prefer a narrowly scoped inline module over compiling mutually exclusive
helpers into a common module.

### Avoid for target-specific helper modules

```rust
fn linux_socket_path() -> &'static str {
    "/run/my-app.sock"
}

fn windows_pipe_name() -> &'static str {
    r"\\.\pipe\my-app"
}

pub fn endpoint_name() -> &'static str {
    #[cfg(target_os = "linux")]
    {
        linux_socket_path()
    }

    #[cfg(target_os = "windows")]
    {
        windows_pipe_name()
    }
}
```

Each target compiles one unused helper.

### Prefer for target-specific helper modules

```rust
#[cfg(target_os = "linux")]
mod endpoint {
    pub(super) fn name() -> &'static str {
        "/run/my-app.sock"
    }
}

#[cfg(target_os = "windows")]
mod endpoint {
    pub(super) fn name() -> &'static str {
        r"\\.\pipe\my-app"
    }
}

#[cfg(not(any(target_os = "linux", target_os = "windows")))]
mod endpoint {
    pub(super) fn name() -> &'static str {
        compile_error!("this example only supports Linux and Windows targets");
    }
}

pub fn endpoint_name() -> &'static str {
    endpoint::name()
}
```

Only the relevant implementation is compiled, the shared surface remains
obvious, and unsupported targets fail explicitly instead of leaving the example
with a missing module.

## Example 3: Test-only helper

Keep test support code inside `#[cfg(test)]` instead of leaving production code
with dead helpers.

### Avoid for test-only helpers

```rust
fn sample_request() -> Request {
    Request::new("ping")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn encodes_ping() {
        let request = sample_request();
        assert_eq!(request.encode(), "ping");
    }
}
```

`sample_request` is dead code in non-test builds.

### Prefer for test-only helpers

```rust
#[cfg(test)]
mod tests {
    use super::*;

    fn sample_request() -> Request {
        Request::new("ping")
    }

    #[test]
    fn encodes_ping() {
        let request = sample_request();
        assert_eq!(request.encode(), "ping");
    }
}
```

The helper now exists only in the compilation mode that uses it.

## Example 4: In-function import inside tests

Use a local import when one test needs one trait or helper.

### Avoid for in-function test imports

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use std::fmt::Write;

    #[test]
    fn formats_status_line() {
        let mut output = String::new();
        write!(&mut output, "{}", Status::Ok).unwrap();
        assert_eq!(output, "200 OK");
    }

    #[test]
    fn preserves_code() {
        assert_eq!(Status::Ok.code(), 200);
    }
}
```

`Write` is only needed by one test.

### Prefer for in-function test imports

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn formats_status_line() {
        use std::fmt::Write;

        let mut output = String::new();
        write!(&mut output, "{}", Status::Ok).unwrap();
        assert_eq!(output, "200 OK");
    }

    #[test]
    fn preserves_code() {
        assert_eq!(Status::Ok.code(), 200);
    }
}
```

The import now documents its true scope and cannot become stray module-level
noise.

## Example 5: Do not paper over mismatched compilation with `allow`

### Avoid for mismatched compilation boundaries

```rust
#[allow(dead_code)]
fn parse_unix_permissions(mode: u32) -> Permissions {
    Permissions::from_mode(mode)
}
```

This silences the symptom while leaving the compiled module dishonest.

### Prefer for mismatched compilation boundaries

```rust
#[cfg(unix)]
fn parse_unix_permissions(mode: u32) -> Permissions {
    Permissions::from_mode(mode)
}
```

If only Unix builds can use the helper, say so in the compilation boundary.

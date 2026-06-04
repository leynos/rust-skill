# Helper Refactor Example

This example covers a common test-helper smell: one function downcasts a
dynamic error source, checks the extracted fields, and panics with custom
messages. Split it into extraction, comparison, and assertion so each part can
be tested independently.

## Original shape

```rust
fn assert_source_matches(
    source: &(dyn Error + 'static),
    expected: ExpectedSource,
) {
    match expected {
        ExpectedSource::Io { message, kind } => {
            let Some(io_source) = source.downcast_ref::<io::Error>() else {
                panic!("io source should be std::io::Error");
            };
            assert_eq!(io_source.kind(), kind);
            assert_eq!(io_source.to_string(), message);
        }
        ExpectedSource::Codec(expected_error) => {
            let Some(codec_source) = source.downcast_ref::<CodecError>() else {
                panic!("codec source should be wireframe::codec::CodecError");
            };
            assert!(
                matches!(codec_source, CodecError::Framing(error) if error == &expected_error),
                "codec source should preserve the original framing error"
            );
        }
    }
}
```

## Refactored shape

First extract a normalized value. Keep it borrowed when the source value is
expensive or impossible to clone.

```rust
#[derive(Debug, PartialEq, Eq)]
enum ActualSource<'a> {
    Io {
        message: String,
        kind: io::ErrorKind,
    },
    Codec {
        error: &'a FramingError,
    },
}

#[derive(Debug, PartialEq, Eq)]
enum SourceExtractionError {
    UnexpectedType,
    UnexpectedCodecVariant,
}

fn extract_source(
    source: &(dyn Error + 'static),
) -> Result<ActualSource<'_>, SourceExtractionError> {
    if let Some(io_source) = source.downcast_ref::<io::Error>() {
        return Ok(ActualSource::Io {
            message: io_source.to_string(),
            kind: io_source.kind(),
        });
    }

    if let Some(codec_source) = source.downcast_ref::<CodecError>() {
        return match codec_source {
            CodecError::Framing(error) => Ok(ActualSource::Codec { error }),
            _ => Err(SourceExtractionError::UnexpectedCodecVariant),
        };
    }

    Err(SourceExtractionError::UnexpectedType)
}
```

Then compare data with a pure function. This function has no panic path and
can be table-tested.

```rust
fn source_matches(
    actual: &ActualSource<'_>,
    expected: &ExpectedSource,
) -> bool {
    match (actual, expected) {
        (
            ActualSource::Io {
                message: actual_message,
                kind: actual_kind,
            },
            ExpectedSource::Io {
                message: expected_message,
                kind: expected_kind,
            },
        ) => actual_kind == expected_kind && actual_message == expected_message,

        (
            ActualSource::Codec {
                error: actual_error,
            },
            ExpectedSource::Codec(expected_error),
        ) => *actual_error == expected_error,

        _ => false,
    }
}
```

Finally keep the assertion wrapper thin. Its job is failure presentation, not
discovery or business logic.

```rust
fn assert_source_matches(
    source: &(dyn Error + 'static),
    expected: ExpectedSource,
) {
    let actual = extract_source(source)
        .expect("source should be a supported error source");

    assert!(
        source_matches(&actual, &expected),
        "source should match expected source\nactual: {actual:?}\nexpected: {expected:?}",
    );
}
```

## Tests unlocked by the split

The extractor can now be asserted directly:

```rust
use pretty_assertions::assert_eq;

let actual = extract_source(source).unwrap();

assert_eq!(
    actual,
    ActualSource::Io {
        message: "permission denied".to_owned(),
        kind: io::ErrorKind::PermissionDenied,
    },
);
```

The comparison can be table-tested without dynamic error values:

```rust
use rstest::rstest;

#[rstest]
#[case::matching_io_source(
    ActualSource::Io {
        message: "permission denied".to_owned(),
        kind: io::ErrorKind::PermissionDenied,
    },
    ExpectedSource::Io {
        message: "permission denied",
        kind: io::ErrorKind::PermissionDenied,
    },
    true
)]
#[case::different_io_kind(
    ActualSource::Io {
        message: "permission denied".to_owned(),
        kind: io::ErrorKind::PermissionDenied,
    },
    ExpectedSource::Io {
        message: "permission denied",
        kind: io::ErrorKind::NotFound,
    },
    false
)]
fn compares_sources(
    #[case] actual: ActualSource<'_>,
    #[case] expected: ExpectedSource,
    #[case] should_match: bool,
) {
    assert_eq!(source_matches(&actual, &expected), should_match);
}
```

If `FramingError` is cheap and cloneable, an owned `ActualSource::Codec {
error: FramingError }` may be simpler. Keep the borrowed version when it avoids
adding clone bounds only for tests.

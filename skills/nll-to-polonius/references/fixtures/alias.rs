pub fn alias(value: &mut String) {
    let first = &mut *value;
    let second = &mut *value;
    first.push('a');
    second.push('b');
}

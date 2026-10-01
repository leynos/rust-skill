pub fn cached(slot: &mut Option<String>) -> &str {
    if let Some(value) = slot.as_deref() {
        return value;
    }
    slot.insert(String::from("value")).as_str()
}

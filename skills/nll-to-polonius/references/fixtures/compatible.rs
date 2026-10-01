pub fn cached(slot: &mut Option<String>) -> &str {
    slot.get_or_insert_with(|| String::from("value")).as_str()
}

pub async fn append(label: &str, output: &mut String) {
    async {}.await;
    output.push_str(label);
}

pub async fn dispatch(fields: &mut (String, String)) {
    append(&fields.0, &mut fields.1).await;
}

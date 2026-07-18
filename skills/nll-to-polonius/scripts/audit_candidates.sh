#!/usr/bin/env bash
# audit_candidates.sh — heuristic scan for NLL-workaround suspects.
#
# Usage: bash audit_candidates.sh /path/to/repo
#
# Output is a list of SUSPECTS grouped by pattern class. Every hit must be
# classified against references/patterns.md before any rewrite; expect most
# hits in well-factored codebases to be refused (see worked-examples.md).

set -euo pipefail

root="${1:?usage: audit_candidates.sh <repo-root>}"
cd "$root"

if command -v rg >/dev/null 2>&1; then
    search() { rg --no-heading --line-number --glob '*.rs' --glob '!target' "$@"; }
else
    search() { grep -rn --include='*.rs' --exclude-dir=target -E "$@" .; }
fi

section() { printf '\n== %s ==\n' "$1"; }

section "Borrowck-blaming comments (read surrounding code)"
search -i 'borrow.?check|borrowck|polonius|appease|NLL|satisfy the borrow' || true

section "Double lookups: contains_key near get/get_mut/insert (patterns.md §2.1)"
search -A4 'contains_key' | grep -E 'get_mut|get\(|insert' || true

section "entry() with cloned/owned key (patterns.md §2.2)"
search '\.entry\([^)]*\.(clone|to_owned|to_string)\(\)' || true

section "Re-lookup after insert with expect/unwrap (patterns.md §2.1)"
search -A3 '\.insert\(' | grep -E 'get(_mut)?\(.*\)\.(expect|unwrap)' || true

section "Index-returning finders (patterns.md §2.4)"
search 'fn [a-z_]*\b(find|locate|slot|index|position)[a-z_]*.*->.*(Option<usize>|usize)' || true

section "drop() of non-guard values / scope-block borrows (patterns.md §2.5)"
search '^\s*drop\(' | grep -viE 'guard|lock|file|handle|writeln|write!' || true

section "Reference-returning lookup fns on &mut self (tier-b API candidates)"
search 'fn [a-z_]+\(&(mut )?self[^)]*\)\s*->\s*(Result<)?&' || true

section "Lookup-shaped fns returning owned values (api-evolution.md §1.1/§1.2)"
search 'fn [a-z_]*(get|find|lookup|fetch|resolve|intern|register)[a-z_]*\(&(mut )?self[^)]*\)\s*->\s*(Result<)?\s*(Option<)?\s*[A-Z]' \
    | grep -vE '\->\s*(Result<)?(Option<)?\s*&' || true

section "Clone-modify-writeback: cloned/cloned() near later insert (api-evolution.md §1.3)"
search -A6 '\.get\([^)]*\)\s*(\.cloned\(\)|\.map\([^)]*clone)' | grep -E '\.insert\(' || true

section "Snapshot-collect before mutation loop (api-evolution.md §1.4)"
search '(keys|iter)\(\)\.cloned\(\)\.collect' || true

section "Clone clusters (top 15 files by clone() count — audit for §2.3)"
if command -v rg >/dev/null 2>&1; then
    rg --count --glob '*.rs' --glob '!target' '\.clone\(\)' \
        | sort -t: -k2 -rn | head -15 || true
else
    grep -rc --include='*.rs' --exclude-dir=target '\.clone()' . \
        | sort -t: -k2 -rn | head -15 || true
fi

printf '\nDone. Classify every suspect (patterns.md §5) before rewriting.\n'

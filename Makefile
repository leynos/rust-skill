.PHONY: markdownlint nixie lint skill-frontmatter-lint skill-metadata-lint skill-manifest-validate skill-manifest-check test

# The skill manifest contract. SKILL_DIRS defaults to every shipped skill and
# can be overridden to check one skill or a test fixture, for example
# `make skill-manifest-check SKILL_DIRS=skills/kani/`.
SKILL_DIRS ?= $(sort $(dir $(wildcard skills/*/SKILL.md)))
SKILLS_REF := uv run --group dev skills-ref
YAMLLINT := uv run --group dev yamllint
METADATA_CHECK := uv run --group dev python tools/check_metadata.py
SKILL_YAMLLINT_CONFIG := {extends: default, rules: {line-length: disable}}

markdownlint:
	markdownlint-cli2 'docs/**/*.md' 'skills/**/*.md' README.md CHANGELOG.md AGENTS.md

nixie:
	nixie .

lint: markdownlint nixie skill-manifest-check

# `set -e` matters: without it the shell loop exits with the status of its final
# iteration, so a conformant trailing skill masks a malformed earlier one.
skill-frontmatter-lint:
	@set -euo pipefail; for skill_dir in $(SKILL_DIRS); do \
		skill_file="$${skill_dir%/}/SKILL.md"; \
		echo "yamllint $$skill_file frontmatter"; \
		awk 'NR == 1 { if ($$0 != "---") exit 1; print; next } $$0 == "---" { found = 1; print; exit } { print } END { if (!found) exit 1 }' "$$skill_file" \
		  | $(YAMLLINT) -d '$(SKILL_YAMLLINT_CONFIG)' -; \
	done

# `skills-ref` rewrites metadata entries with `str(v)` rather than rejecting the
# shapes the Agent Skills schema forbids, so a list or mapping value would pass
# validation and reach consumers as a Python repr. Check the shape first.
skill-metadata-lint:
	@set -eu; for skill_dir in $(SKILL_DIRS); do \
		$(METADATA_CHECK) "$${skill_dir%/}"; \
	done

skill-manifest-validate:
	@set -eu; for skill_dir in $(SKILL_DIRS); do \
		echo "skills-ref validate $$skill_dir"; \
		$(SKILLS_REF) validate "$$skill_dir"; \
	done

skill-manifest-check: skill-frontmatter-lint skill-metadata-lint skill-manifest-validate

test:
	uv run --group dev pytest

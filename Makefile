.PHONY: markdownlint nixie

markdownlint:
	markdownlint-cli2 'docs/**/*.md' 'skills/**/*.md' README.md CHANGELOG.md

nixie:
	nixie .

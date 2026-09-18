.PHONY: install verify-lock license-audit test

install:
	cd niyamtrace && uv sync --frozen --all-extras

verify-lock:
	cd niyamtrace && uv lock --locked

license-audit:
	cd niyamtrace && pip-licenses --with-authors --with-urls

test:
	cd niyamtrace && pytest tests/ -v

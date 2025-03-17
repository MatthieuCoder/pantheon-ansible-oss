ansible-galaxy-deps: roles/requirements.yml
	ansible-galaxy install -r ./roles/requirements.yml --force
.PHONY: ansible-galaxy-deps

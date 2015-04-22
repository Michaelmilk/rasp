cd ..
sphinx-apidoc -f -e -o docs\_apidoc pinic
cd docs
make html && start _build\html\index.html

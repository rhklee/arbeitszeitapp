{ buildPythonPackage, pytestCheckHook

# python packages
, deepdiff, email_validator, flask, flask-babel, flask-talisman, flask_login
, flask_mail, flask_migrate, flask-restx, flask_wtf, is_safe_url, matplotlib
, sphinx, flask-profiler, typing-extensions, parameterized, Babel, setuptools }:
buildPythonPackage {
  pname = "arbeitszeitapp";
  version = "0.0.0";
  src = ../..;
  outputs = [ "out" "doc" ];
  postPhases = [ "buildDocsPhase" ];
  format = "pyproject";
  buildInputs = [ pytestCheckHook sphinx parameterized Babel setuptools ];
  propagatedBuildInputs = [
    deepdiff
    email_validator
    flask
    flask-babel
    flask-talisman
    flask_login
    flask_mail
    flask_migrate
    flask-restx
    flask_wtf
    is_safe_url
    matplotlib
    typing-extensions
  ];
  buildDocsPhase = ''
    mkdir -p $doc/share/doc/arbeitszeitapp
    python -m sphinx -a $src/docs $doc/share/doc/arbeitszeitapp
  '';
  passthru.optional-dependencies = { profiling = [ flask-profiler ]; };
  DISABLED_TESTS = "database_required";
}

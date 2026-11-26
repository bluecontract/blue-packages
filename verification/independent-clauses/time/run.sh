#!/usr/bin/env bash
set -euo pipefail

fixture_dir=$(cd "$(dirname "$0")" && pwd)
catalogue_root=${1:?Pass the frozen Blue Packages checkout}
classpath_file=${2:?Pass the frozen Core test classpath file}
classpath=$(cat "$classpath_file")
classes=$(mktemp -d)
trap 'rm -rf "$classes"' EXIT

java_bin=${JAVA_HOME:+$JAVA_HOME/bin/}
"${java_bin}javac" -cp "$classpath" -d "$classes" \
  "$catalogue_root/tools/QualificationRuntime.java" \
  "$catalogue_root/tools/CurrentOperationScenarios.java" \
  "$fixture_dir/ClockCompositionProof.java"
"${java_bin}java" -Xmx1500m -cp "$classes:$classpath" blue.core.ClockCompositionProof \
  "$catalogue_root" "$fixture_dir" "${@:3}"

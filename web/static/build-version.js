// Bump PR_OS_BUILD_VERSION on each static deploy that should bust browser cache.
window.PR_OS_BUILD_VERSION = "20260624-35";
window.PR_OS_BUILD_VERSION_PREVIOUS = "20260624-34";

window.prOsBuildVersion = function prOsBuildVersion() {
  return window.PR_OS_BUILD_VERSION || window.PR_OS_BUILD_VERSION_PREVIOUS;
};

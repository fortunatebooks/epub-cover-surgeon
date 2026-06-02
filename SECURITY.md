# Security Policy

## Supported versions

Security fixes are accepted for the latest released minor version.

## Reporting a vulnerability

Please open a private security advisory on GitHub or email the maintainer listed in the repository profile.

Do **not** attach private, copyrighted, or otherwise non-redistributable EPUB files to public issues. If a malformed EPUB demonstrates a vulnerability, please provide a minimized synthetic fixture or describe the ZIP/XML structure needed to reproduce it.

## ZIP/XML handling scope

EPUB Cover Surgeon validates ZIP member paths, archive size, entry count, and package XML before cover operations. It does not execute EPUB content, fetch remote resources, bypass DRM, or render HTML/CSS.

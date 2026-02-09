This document summarizes the shared notification utility and linting setup.

Shared notification utility
--------------------------
- `static/js/shared_notification.js` provides a centralized `showNotification(message, type)` function.
- It also exposes:
  - `window.RiskMap.showNotification(message, type)` (namespaced API)
  - `window.showNotification(message, type)` (global alias)
  - `window.showAlert(type, message)` (backwards-compatible alias; type is first param)

This avoids duplicated implementations and ensures consistent styling and behavior across templates.

How to include it
-----------------
- Most templates inherit from `base_navigation.html`, which already has a `<script src="/static/js/shared_notification.js"></script>` include.
- For pages that do not extend the base, ensure they include the script tag before any code that calls `showNotification` or `showAlert`.

ESLint and CI
-------------
- `package.json` includes a `lint` script that runs ESLint on JS and HTML templates:
  - `npm install` will install `eslint` and `eslint-plugin-html`.
  - `npm run lint` will run the linter.
- A GitHub Actions workflow has been added at `.github/workflows/eslint.yml` to run lint checks and inline JS validation using `tools/check_js_with_node.js` on pushes and PRs.

Notes & Best Practices
----------------------
- Prefer using `showNotification(message, type)` in code for clarity and to avoid argument ordering confusion.
- If maintaining legacy code, `showAlert(type, message)` will still work due to the wrapper.
- Add new notifications using `showNotification('Message here', 'info|success|warning|error')`.
- Consider standardizing colors and transitions in a CSS file rather than inline styles in `shared_notification.js`.


If you'd like, I can:
- Migrate all existing Bootstrapped `alert` usage to `showNotification` or create a `useBootstrap` switch in the shared script.
- Add a minimal `package-lock.json` or advise on adding dev dependencies for CI.

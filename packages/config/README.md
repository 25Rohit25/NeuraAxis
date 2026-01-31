# @neuraxis/config

> Shared Configuration Files for NEURAXIS

## Overview

This package contains shared configuration files used across NEURAXIS packages and applications.

## Configurations

### ESLint
Shared ESLint configuration with TypeScript and React support.

```js
// .eslintrc.js
module.exports = {
  extends: ["@neuraxis/config/eslint"],
};
```

### TypeScript
Base TypeScript configuration to extend from.

```json
{
  "extends": "@neuraxis/config/typescript"
}
```

### Tailwind CSS
Shared Tailwind CSS configuration.

```js
// tailwind.config.js
module.exports = require("@neuraxis/config/tailwind");
```

## Files

- `eslint.config.js` - ESLint configuration
- `tsconfig.base.json` - Base TypeScript configuration
- `tailwind.config.js` - Tailwind CSS preset

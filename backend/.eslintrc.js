module.exports = {
  env: {
    node: true,
    es2021: true,
  },
  extends: 'airbnb-base',
  parserOptions: {
    ecmaVersion: 'latest',
  },
  rules: {
    indent: ['error', 2],
    semi: ['error', 'always'],
    'no-console': 'off',
    'no-underscore-dangle': ['error', { allow: ['_id'] }],
  },
};
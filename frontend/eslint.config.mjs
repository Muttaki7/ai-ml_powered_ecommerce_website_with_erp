import next from "eslint-config-next";

export default [
  { ignores: ["eslint.config.mjs"] },
  ...next,
  {
    rules: {
      "@next/next/no-img-element": "off",
    },
  },
];
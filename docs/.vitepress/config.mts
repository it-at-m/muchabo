import { defineConfig } from "vitepress"

export default defineConfig({
  title: "muchabo",
  description: "Documentation for muchabo",
  themeConfig: {
    nav: [{ text: "Home", link: "/" }],
    sidebar: [{ text: "Introduction", items: [{ text: "Home", link: "/" }] }],
  },
})

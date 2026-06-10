/// <reference types="vite/client" />

declare module "*.css" {}

declare module "*.glsl?raw" {
  const content: string
  export default content
}
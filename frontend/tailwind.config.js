/** @type {import('tailwindcss').Config} */
import tailwindForms from '@tailwindcss/forms';
import tailwindContainerQueries from '@tailwindcss/container-queries';

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
      extend: {
          "colors": {
              "on-secondary-fixed-variant": "#3d4c09",
              "tertiary-fixed-dim": "#74d7cb",
              "outline": "#8c716e",
              "surface-tint": "#ac322f",
              "surface-container": "#ffe9e7",
              "on-secondary-fixed": "#161e00",
              "on-tertiary": "#ffffff",
              "surface-dim": "#ecd5d2",
              "surface-bright": "#fff8f7",
              "on-background": "#251817",
              "error": "#ba1a1a",
              "background": "#fff8f7",
              "secondary-fixed": "#d7eb98",
              "tertiary-fixed": "#90f4e7",
              "surface": "#fff8f7",
              "on-surface": "#251817",
              "on-primary-fixed": "#410003",
              "error-container": "#ffdad6",
              "primary-container": "#cc4944",
              "on-surface-variant": "#58413f",
              "tertiary": "#006961",
              "surface-container-lowest": "#ffffff",
              "on-secondary-container": "#586925",
              "surface-container-high": "#fbe3e0",
              "inverse-surface": "#3b2d2c",
              "on-tertiary-fixed-variant": "#00504a",
              "on-secondary": "#ffffff",
              "on-primary": "#ffffff",
              "primary": "#aa312e",
              "surface-container-highest": "#f5dddb",
              "secondary-fixed-dim": "#bbcf7f",
              "secondary": "#546521",
              "on-tertiary-fixed": "#00201d",
              "outline-variant": "#e0bfbc",
              "on-tertiary-container": "#fbfffd",
              "inverse-on-surface": "#ffedeb",
              "primary-fixed-dim": "#ffb3ad",
              "surface-container-low": "#fff0ef",
              "inverse-primary": "#ffb3ad",
              "tertiary-container": "#00847a",
              "on-primary-fixed-variant": "#8b191b",
              "secondary-container": "#d4e896",
              "on-error": "#ffffff",
              "on-error-container": "#93000a",
              "primary-fixed": "#ffdad6",
              "on-primary-container": "#fffeff",
              "surface-variant": "#f5dddb"
          },
          "borderRadius": {
              "DEFAULT": "0.125rem",
              "lg": "0.25rem",
              "xl": "0.5rem",
              "full": "0.75rem"
          },
          "spacing": {
              "xl": "40px",
              "gutter": "24px",
              "xxl": "64px",
              "lg": "24px",
              "sm": "8px",
              "margin-desktop": "48px",
              "unit": "4px",
              "xs": "4px",
              "margin-mobile": "16px",
              "md": "16px"
          },
          "fontFamily": {
              "body-lg": ["Manrope"],
              "body-sm": ["Manrope"],
              "headline-lg": ["Newsreader"],
              "headline-lg-mobile": ["Newsreader"],
              "headline-md": ["Manrope"],
              "label-md": ["Manrope"],
              "display-lg": ["Newsreader"],
              "body-md": ["Manrope"]
          },
          "fontSize": {
              "body-lg": ["18px", { "lineHeight": "1.6", "fontWeight": "400" }],
              "body-sm": ["14px", { "lineHeight": "1.5", "fontWeight": "400" }],
              "headline-lg": ["32px", { "lineHeight": "1.2", "fontWeight": "500" }],
              "headline-lg-mobile": ["28px", { "lineHeight": "1.2", "fontWeight": "500" }],
              "headline-md": ["24px", { "lineHeight": "1.4", "fontWeight": "600" }],
              "label-md": ["12px", { "lineHeight": "1", "letterSpacing": "0.05em", "fontWeight": "700" }],
              "display-lg": ["48px", { "lineHeight": "1.1", "letterSpacing": "-0.02em", "fontWeight": "600" }],
              "body-md": ["16px", { "lineHeight": "1.6", "fontWeight": "400" }]
          }
      }
  },
  plugins: [
    tailwindForms,
    tailwindContainerQueries,
  ],
}

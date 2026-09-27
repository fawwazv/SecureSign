import type { Preview } from '@storybook/vue3'
import '../src/assets/styles/main.css'

const preview: Preview = {
  parameters: {
    controls: { matchers: { color: /(background|color)$/i, date: /Date$/i } },
    backgrounds: {
      default: 'white',
      values: [
        { name: 'white', value: '#FFFFFF' },
        { name: 'cream', value: '#FFF1E7' },
        { name: 'deep-blue', value: '#326080' },
      ],
    },
  },
}

export default preview

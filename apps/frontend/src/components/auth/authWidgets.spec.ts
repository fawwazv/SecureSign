import { describe, expect, it, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import GoogleSignInButton from '@/components/auth/GoogleSignInButton.vue'
import TurnstileWidget from '@/components/auth/TurnstileWidget.vue'

beforeEach(() => {
  vi.restoreAllMocks()
  delete (window as unknown as { google?: unknown }).google
  delete (window as unknown as { turnstile?: unknown }).turnstile
})

describe('GoogleSignInButton (FE1-5)', () => {
  it('render GIS button dan emit credential', async () => {
    vi.stubEnv('VITE_GOOGLE_CLIENT_ID', 'test-client-id')
    let cb: (r: { credential?: string }) => void = () => {}
    const renderButton = vi.fn()
    ;(window as unknown as { google: unknown }).google = {
      accounts: {
        id: {
          initialize: (o: { callback: typeof cb }) => {
            cb = o.callback
          },
          renderButton,
        },
      },
    }
    const w = mount(GoogleSignInButton)
    await w.vm.$nextTick()
    expect(renderButton).toHaveBeenCalled()
    cb({ credential: 'tok123' })
    expect(w.emitted('credential')).toEqual([['tok123']])
    vi.unstubAllEnvs()
  })

  it('fallback jika script/client-id belum siap', async () => {
    vi.stubEnv('VITE_GOOGLE_CLIENT_ID', '')
    const w = mount(GoogleSignInButton)
    await w.vm.$nextTick()
    expect(w.text()).toContain('tidak dapat dimuat')
    vi.unstubAllEnvs()
  })
})

describe('TurnstileWidget (FE1-5)', () => {
  it('render + emit verified', async () => {
    let cb: (t: string) => void = () => {}
    const render = vi.fn((_el: unknown, o: { callback: typeof cb }) => {
      cb = o.callback
      return 'wid-1'
    })
    ;(window as unknown as { turnstile: unknown }).turnstile = { render, reset: vi.fn() }
    const w = mount(TurnstileWidget, { props: { siteKey: 'test-key' } })
    await w.vm.$nextTick()
    expect(render).toHaveBeenCalled()
    cb('cap-tok')
    expect(w.emitted('verified')).toEqual([['cap-tok']])
  })

  it('mode dev tanpa key: tampilkan pesan, tidak crash', async () => {
    vi.stubEnv('VITE_CAPTCHA_SITE_KEY', '')
    const w = mount(TurnstileWidget, { props: { siteKey: '' } })
    await w.vm.$nextTick()
    expect(w.text()).toContain('belum dikonfigurasi')
    vi.unstubAllEnvs()
  })
})

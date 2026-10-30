import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
afterEach(() => { cleanup(); sessionStorage.clear(); localStorage.clear() })

// Presentation-only browser APIs needed by school forms in jsdom.
Object.defineProperty(window, 'matchMedia', { writable: true, value: (query: string) => ({matches:false,media:query,onchange:null,addListener() {},removeListener() {},addEventListener() {},removeEventListener() {},dispatchEvent:()=>false}) })
class ResizeObserverStub { observe() {} unobserve() {} disconnect() {} }
Object.defineProperty(globalThis, 'ResizeObserver', { writable: true, value: ResizeObserverStub })

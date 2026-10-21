import '@testing-library/jest-dom';

// Polyfills and mocks for React Flow in Vitest / jsdom environment
if (typeof window !== 'undefined') {
  if (!window.ResizeObserver) {
    window.ResizeObserver = class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    };
  }

  if (typeof window.DOMMatrixReadOnly === 'undefined') {
    // @ts-expect-error Mocking DOMMatrixReadOnly for jsdom
    window.DOMMatrixReadOnly = class DOMMatrixReadOnly {
      m11 = 1;
      m22 = 1;
      m41 = 0;
      m42 = 0;
    };
  }

  // React Flow SVG measurement mock
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const svgProto = SVGElement.prototype as any;
  if (typeof SVGElement !== 'undefined' && !svgProto.getBBox) {
    svgProto.getBBox = () => ({
      x: 0,
      y: 0,
      width: 100,
      height: 40,
      bottom: 40,
      left: 0,
      right: 100,
      top: 0,
      toJSON: () => {},
    });
  }
}

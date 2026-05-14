/**
 * API ベース URL。
 * - 開発: 未設定なら空文字（Vite の /api プロキシ経由で同一オリジン）
 * - 本番ビルド: 未設定なら http://127.0.0.1:8001（必要なら VITE_API_URL で上書き）
 */
export const API_URL =
  import.meta.env.VITE_API_URL !== undefined
    ? import.meta.env.VITE_API_URL
    : import.meta.env.DEV
      ? ''
      : 'http://127.0.0.1:8001'

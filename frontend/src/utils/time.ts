/**
 * 后端 SQLite 存储的 datetime 无时区标识，实际是 UTC 时间。
 * JavaScript new Date() 无 Z 后缀时会按本地时区解析，导致偏移。
 * 手动补 Z 后缀后，通过 Asia/Shanghai 格式化为北京时间显示。
 */

/** 格式化为北京时间完整字符串（日期+时间） */
export function formatBeijingTime(isoString: string): string {
  const utcStr = isoString.endsWith('Z') ? isoString : isoString + 'Z'
  return new Date(utcStr).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

/** 格式化为北京时间日期（仅日期，不含时间） */
export function formatBeijingDate(isoString: string): string {
  const utcStr = isoString.endsWith('Z') ? isoString : isoString + 'Z'
  return new Date(utcStr).toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

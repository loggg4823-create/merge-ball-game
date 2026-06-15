export interface Todo {
  /** 唯一标识 */
  id: string;
  /** 待办内容 */
  text: string;
  /** 是否已完成 */
  completed: boolean;
  /** 创建时间戳 */
  createdAt: number;
}

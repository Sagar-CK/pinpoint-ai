
/**
 * A message in a search session.
 */
export interface IMessage {
    id: string;
    content: string;
    createdAt: Date;
    updatedAt: Date;
    senderId: string;
    sessionId: string;
}
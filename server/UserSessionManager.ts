import { WebSocket } from "ws";

// Define ISession types
export interface ISession {
  id: string;
  createdAt: Date;
  lastActive: Date;
  data: Record<string, any>;
  ws: WebSocket;
}

// In-memory database
export class UserSessionManager {
  private ISessions: Map<string, ISession>;

  constructor() {
    this.ISessions = new Map();
  }

  createSession(ws: WebSocket): ISession {
    const ISessionId = Math.random().toString(36).substring(2, 15);
    const ISession: ISession = {
      id: ISessionId,
      createdAt: new Date(),
      lastActive: new Date(),
      data: {},
      ws,
    };
    this.ISessions.set(ISessionId, ISession);
    return ISession;
  }

  getSession(ISessionId: string): ISession | undefined {
    return this.ISessions.get(ISessionId);
  }

  updateSession(ISessionId: string, data: Partial<Record<string, any>>): void {
    const ISession = this.ISessions.get(ISessionId);
    if (ISession) {
      ISession.lastActive = new Date();
      ISession.data = { ...ISession.data, ...data };
      this.ISessions.set(ISessionId, ISession);
    }
  }

  deleteSession(ISessionId: string): boolean {
    return this.ISessions.delete(ISessionId);
  }

  getAllSessions(): ISession[] {
    return Array.from(this.ISessions.values());
  }
}

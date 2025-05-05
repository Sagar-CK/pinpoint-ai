import { WebSocketServer, WebSocket } from "ws";
import { UserSessionManager } from "./UserSessionManager";
import { SearchSessionManager } from "./SearchSessionManager";
import { SearchHandler } from "./SearchHandler";

// Create session store instance
const userSessionManager = new UserSessionManager();
const searchSessionManager = new SearchSessionManager();
const searchHandler = new SearchHandler();

// Create WebSocket server
const wss = new WebSocketServer({
  port: 1337,
  perMessageDeflate: false,
  clientTracking: true,
});

console.log("Server is running on port 1337");
wss.on("connection", function connection(ws) {
  // Create a new session for each connection
  const session = userSessionManager.createSession(ws);
  console.log(`New user session created: ${session.id}`);

  ws.on("message", async function message(data) {
    try {
      const parsedData = JSON.parse(data.toString());
      // Update session data
      userSessionManager.updateSession(session.id, parsedData);
      console.log(`Message from user '${session.id}': `, parsedData);

      // Handle NEW_SEARCH_SESSION message
      switch (parsedData.type) {
        case "NEW_SEARCH_SESSION":
          handleCreateSearchSession(ws, parsedData, session.id);
          break;

        case "JOIN_SEARCH_SESSION":
          handleJoinSearchSession(ws, parsedData, session.id);
          break;

        case "ADJUST_SEARCH_SESSION":
          handleAdjustSearchSession(ws, parsedData, session.id);
          break;

        // Handle unrecognized message types
        default:
          ws.send(
            JSON.stringify({
              type: "error",
              message: "Unrecognized message type",
            }),
          );
      }
    } catch (error) {
      console.error("Error processing message:", error);
      ws.send(
        JSON.stringify({ type: "error", message: "Invalid message format" }),
      );
    }
  });

  ws.on("close", () => {
    // Clean up session when connection closes
    userSessionManager.deleteSession(session.id);
    console.log(`Session ${session.id} closed and deleted`);
  });

  // Send initial session information
  ws.send(
    JSON.stringify({
      type: "userSessionCreated",
      sessionId: session.id,
    }),
  );
});

const handleCreateSearchSession = async (
  ws: WebSocket,
  parsedData: any,
  userSessionId: string,
) => {
  const places = await searchHandler.searchMaps(parsedData.query);
  const searchSession = searchSessionManager.createSearch(
    parsedData.query,
    userSessionId,
    places,
  );
  console.log(
    `'${userSessionId}' created search session '${searchSession.id}'`,
  );

  // Send back the search session information and results
  ws.send(
    JSON.stringify({
      type: "searchSessionCreated",
      session: searchSession,
    }),
  );
};

const handleJoinSearchSession = async (
  ws: WebSocket,
  parsedData: any,
  userSessionId: string,
) => {
  const searchSessionId = parsedData.searchSessionId;
  const searchSession = searchSessionManager.getSearch(searchSessionId);

  if (searchSession) {
    try {
      searchSessionManager.joinSearch(searchSessionId, userSessionId);
      const searchSession = searchSessionManager.getSearch(searchSessionId);

      if (!searchSession) {
        throw new Error("Search session not found");
      }

      // Tell all users in the search session that the user has joined
      searchSession.userSessionIds.map(async (userId) => {
        const userSession = userSessionManager.getSession(userId);
        if (userSession) {
          userSession.ws.send(
            JSON.stringify({
              type: "searchSessionUpdated",
              session: searchSession,
            }),
          );
        }
      });
    } catch (error) {
      console.error("Error processing search:", error);
      ws.send(
        JSON.stringify({
          type: "error",
          message: "Error processing search request",
        }),
      );
    }
  } else {
    ws.send(
      JSON.stringify({
        type: "error",
        message: "Search session not found",
      }),
    );
  }
};

const handleAdjustSearchSession = async (
  ws: WebSocket,
  parsedData: any,
  userSessionId: string,
) => {
  const searchSessionId = parsedData.searchSessionId;
  const prompt = parsedData.prompt;
  const searchSession = searchSessionManager.getSearch(searchSessionId);

  if (!searchSession) {
    ws.send(
      JSON.stringify({
        type: "error",
        message: "Search session not found",
      }),
    );
    return;
  }

  const session = await searchSessionManager.adjustSearch(
    searchSessionId,
    userSessionId,
    prompt,
  );

  ws.send(
    JSON.stringify({
      type: "searchSessionAdjusted",
      session: session,
    }),
  );

  // Distribute the updated session to all users in the search
  for (const userId of session.userSessionIds) {
    const userSession = userSessionManager.getSession(userId);
    if (userSession) {
      userSession.ws.send(
        JSON.stringify({
          type: "searchSessionUpdated",
          session: session,
        }),
      );
    }
  }
};

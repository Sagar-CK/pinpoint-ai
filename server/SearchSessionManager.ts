import { IMessage } from "./models/IMessage";
import { SearchHandler } from "./SearchHandler";

/**
 * Represents a collaborative search effort between multiple users.
 *
 */
export interface ISearch {
  id: string;
  createdAt: Date;
  updatedAt: Date;
  query: string;

  /**
   * ID of the user session that created this search.
   */
  createdBy: string;

  /**
   * IDs of the user sessions that are part of this search.
   */
  userSessionIds: string[];

  /**
   * Places in the search.
   */
  places: any[];

  /**
   * Ranking of the places.
   */
  ranking: number[];

  /**
   * User-specific prompts for the search. Each prompt is a reduction of all previous prompts.
   */
  userPrompts: Record<string, string>;
  
  /**
   * Chat history for the search ordered by timestamp.
   */
  chatHistory: Record<number, IMessage>;

  /**
   * User-specific relevance matrix. Each row corresponds to a user prompt, and each column corresponds to a place,
   * with cell [i, j] being the relevance score for the prompt i and place j.
   */
  relevanceMatrix: number[][];
}

// In-memory database for searches
export class SearchSessionManager {
  private searches: Map<string, ISearch>;
  private searchHandler: SearchHandler;

  constructor() {
    this.searches = new Map();
    this.searchHandler = new SearchHandler();
  }

  private randomId(): string {
    return Math.random().toString(36).substring(2, 15);
  }

  createSearch(query: string, user: string, places: any[]): ISearch {
    const search: ISearch = {
      id: this.randomId(),
      createdAt: new Date(),
      updatedAt: new Date(),
      query: query,
      createdBy: user,
      userSessionIds: [user], // invariant
      ranking: Array.from({length: places.length}, (_, i) => i + 1), // transient on relevance matrix
      userPrompts: { [user]: "" },
      chatHistory: {},
      relevanceMatrix: [places.map(_ => 1)],
      places: places, // invariant
    };
    this.searches.set(search.id, search);
    return search;
  }

  getSearch(searchId: string): ISearch | undefined {
    return this.searches.get(searchId);
  }

  /**
   * Returns the column index of the user session in the relevance matrix.
   * @param userSessionId The ID of the user session.
   * @param search The search session.
   * @returns The column index of the user session in the relevance matrix.
   */
  private getUserColumn(userSessionId: string, search: ISearch): number {
    return search.userSessionIds.indexOf(userSessionId);
  }

  /**
   * Adds a user session to a search.
   * @param searchId The ID of the search.
   * @param userSessionId The ID of the user session to add.
   */
  joinSearch(searchId: string, userSessionId: string) {
    const search = this.searches.get(searchId);
    if (search) {
      search.userSessionIds.push(userSessionId);
      search.userPrompts[userSessionId] = "";
      search.relevanceMatrix.push(search.places.map(_ => 1));
      this.searches.set(searchId, search);
    }
  }

  updateSearch(searchId: string, data: Partial<ISearch>): void {
    const search = this.searches.get(searchId);
    if (search) {
      search.updatedAt = new Date();
      Object.assign(search, data);
      this.searches.set(searchId, search);
    }
  }

  /**
   * Adjusts the relevance matrix based on the user's prompt.
   * @param searchId The ID of the search.
   * @param userSessionId The ID of the user session.
   * @param prompt The prompt from the user.
   * @returns The updated places in ranking order.
   */
  async adjustSearch(searchId: string, userSessionId: string, prompt: string): Promise<ISearch> {
    // Get the search session
    const search = this.searches.get(searchId);
    if (!search) {
        throw new Error("Search not found");
      }
      
    // 1. Combine the new user prompt with previous user prompts into a single prompt
    // TODO: try using SearchHandler.getCombinedUserPrompt
    const previousPrompt = search.userPrompts[userSessionId];
    if (!previousPrompt) {
        search.userPrompts[userSessionId] = prompt;
    } else {
        search.userPrompts[userSessionId] = `${previousPrompt}\n${prompt}`;
    }

    // 2. Apply the prompt to the relevance matrix
    const col = this.getUserColumn(userSessionId, search);
    const updatedColumn = await Promise.all(search.relevanceMatrix[col].map(async (row, index) => {
        const place = search.places[index];
        const relevance = await this.searchHandler.getRelevance(place, search.query, prompt);
        return relevance;
    }));
    console.log(`User ${userSessionId} updated column: ${JSON.stringify(updatedColumn)}`);

    // 3. Update the search session with the new column and prompt
    search.relevanceMatrix[col] = updatedColumn.map(r => r.relevance);
    search.userPrompts[userSessionId] = prompt;
    search.ranking = this.rankPlaces(search);
    this.searches.set(searchId, search);
    console.log(`User ${userSessionId} ranking: ${JSON.stringify(search.ranking)}`);

    return search;
  }

  /**
   * Calculates the current ranking of the places by averaging the relevance scores.
   * @param search The search session.
   * @returns The places in ranking order.
   */
  private rankPlaces(search: ISearch): number[] {
    const places = search.places;
    const relevanceMatrix = search.relevanceMatrix;

    // Calculate the average relevance score for each place across all users
    const totalScores = places.map((_, index) => {
      const totalScore = relevanceMatrix.reduce((sum, row) => sum + row[index], 0);
      const averageScore = totalScore / relevanceMatrix.length; // Divide by number of users
      return { index, totalScore: averageScore };
    });

    // Sort places by total relevance score in descending order
    totalScores.sort((a, b) => b.totalScore - a.totalScore);
    return totalScores.map(({ index }) => index);
  }

  deleteSearch(searchId: string): boolean {
    return this.searches.delete(searchId);
  }

  getAllSearches(): ISearch[] {
    return Array.from(this.searches.values());
  }
}

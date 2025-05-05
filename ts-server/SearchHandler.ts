import { GoogleGenAI, Type } from "@google/genai";
import OpenAI from "openai";
import { zodResponseFormat } from "openai/helpers/zod";
import { z } from "zod";
const openai = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY!,
});


type RelevanceResultType = {
    relevance: number;
    reason: string;
}
const RelevanceResultSchema: z.ZodType<RelevanceResultType> = z.lazy(() => z.object({
  relevance: z.number().describe("A number between 1.0 and 10.0 indicating the relevance of the place to the user prompt."),
  reason: z.string().describe("A string explaining the relevance of the place to the search and user prompt."),
}));

export class SearchHandler {
  private genAI: GoogleGenAI;
  private googleApiKey: string = process.env.GOOGLE_API_KEY!;
  private googlePlacesApiUrl: string =
    "https://places.googleapis.com/v1/places:searchText?fields=*";

  constructor() {
    this.genAI = new GoogleGenAI({
      apiKey: this.googleApiKey,
    });
  }

  /**
   * Makes a call to the Google Maps API to search for places.
   * @param searchQuery The search query to search for.
   * @returns A list of places.
   */
  public async searchMaps(searchQuery: string): Promise<any[]> {
    const headers = {
      Accept: "application/json",
      "Content-Type": "application/json",
      "X-Goog-Api-Key": this.googleApiKey
    };

    const body = {
      textQuery: searchQuery,
    };

    try {
      const response = await fetch(
        this.googlePlacesApiUrl,
        {
          method: "POST",
          headers,
          body: JSON.stringify(body),
        },
      );

      if (!response.ok) {
        console.error(response);
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const json = await response.json() as { places: any[] };
      return json.places;
    } catch (error) {
      console.error("Error fetching places:", error);
      throw error;
    }
  }

  /**
   * Semantically combines two user prompts into a single prompt.
   * @param previousPrompt The previous user prompt.
   * @param newPrompt The new user prompt.
   * @returns The combined user prompt.
   */
  public async getCombinedUserPrompt(previousPrompt: string, newPrompt: string): Promise<string> {
    const response = await this.genAI.models.generateContent({
        model: 'gemini-2.0-flash',
        contents: [{
            role: "system",
            parts: [{text: `You are a helpful assistant that is given two prompts containing prefferences for choosing a place (e.g. restaurant, club, museum, etc...). Your task is to combine the two prompts into a single prompt without losing any crucial information.
                The previous prompt is ${previousPrompt} and the new prompt is ${newPrompt}.`}]
        }],
        config: {
            temperature: 0.05
        }
    })

    if (!response.text) {
        throw new Error("getCombinedUserPrompt - No response from Gemini");
    }
    
    return response.text
}

  /**
   * Applies a user prompt to a specific place to retrieve a relevance score.
   * @param place The place to apply the prompt to.
   * @param searchPrompt The base prompt for the search.
   * @param userPrompt The prompt to apply to the place.
   * @returns The relevance score.
   */
  public async getRelevance(place: any, searchPrompt: string, userPrompt: string): Promise<RelevanceResultType> {
    console.log(process.env.OPENROUTER_API_KEY);
    const response = await openai.chat.completions.create({
      model: "gpt-4o",
      messages: [
        {
          role: "system",
          content: `You are a judge of relevance. You are looking for a place that matches the following prompt: ${searchPrompt}. 
          Given the information about a place below and specific preferences from the user evaluate the relevance of the place on a scale from 1.0 to 10.0.
          
          Place: ${JSON.stringify(place)}`
        },
        {
          role: "user",
          content: userPrompt
        }
      ],
      response_format: zodResponseFormat(RelevanceResultSchema, "relevance_result")
    });

    
    if (!response || !response.choices[0].message.content) {
      throw new Error("No content received from OpenAI");
    }
    
    try {
      const result = JSON.parse(response.choices[0].message.content);
      return {
        reason: result.reason,
        relevance: result.relevance
      };
    } catch (error) {
      throw new Error("Failed to parse OpenAI response as JSON");
    }
  }
}

const API_URL = import.meta.env.VITE_API_URL;

export type ReviewType =
    | "repository"
    | "code"
    | "deep";

export async function analyzeRepository(repository: string) {
  const response = await fetch(`${API_URL}/repository-review`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      repository,
      depth: "medium",
    }),
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  const data = await response.json();

  return data;}

export function extractReportText(data: any) {
  if (typeof data?.response?.response === "string") {
    return data.response.response;
  }

  if (typeof data?.report === "string") {
    return data.report;
  }

  if (typeof data?.response === "string") {
    return data.response;
  }

  return JSON.stringify(data, null, 2);
}

export async function analyzeCode(
    repository: string
) {

    const response = await fetch(`${API_URL}/code-review`, {

        method: "POST",

        headers: {

            "Content-Type": "application/json",

        },

        body: JSON.stringify({

            repository,

            depth: "medium",

        }),

    });

    if (!response.ok) {

        const message = await response.text();

        throw new Error(message || `Request failed with ${response.status}`);

    }

    return await response.json();

}

export async function analyzeDeepCode(
    repository: string
) {

    const response = await fetch(`${API_URL}/code-review`, {

        method: "POST",

        headers: {

            "Content-Type": "application/json",

        },

        body: JSON.stringify({

            repository,

            depth: "deep",

        }),

    });

    if (!response.ok) {

        const message = await response.text();

        throw new Error(message || `Request failed with ${response.status}`);

    }

    return await response.json();

}
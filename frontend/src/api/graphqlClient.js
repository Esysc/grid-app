import { GraphQLClient } from 'graphql-request';

/**
 * GraphQL client for Grid Monitor API
 * Handles authentication and request setup
 */
class GraphQLClientWrapper {
  constructor() {
    this.client = null;
    this.token = null;
  }

  /**
   * Initialize or update the GraphQL client with auth token
   * @param {string} token - JWT access token
   */
  setToken(token) {
    this.token = token;
    const endpoint = '/graphql';
    
    this.client = new GraphQLClient(endpoint, {
      headers: token ? {
        'Authorization': `Bearer ${token}`
      } : {}
    });
  }

  /**
   * Execute a GraphQL query
   * @param {string} query - GraphQL query string
   * @param {object} variables - Query variables
   * @returns {Promise<any>} Query result
   */
  async request(query, variables = {}) {
    if (!this.client) {
      throw new Error('GraphQL client not initialized. Call setToken() first.');
    }

    try {
      return await this.client.request(query, variables);
    } catch (error) {
      // Handle 401 errors for token expiration
      if (error.response?.status === 401) {
        throw new Error('TOKEN_EXPIRED');
      }
      throw error;
    }
  }

  /**
   * Execute a GraphQL mutation
   * @param {string} mutation - GraphQL mutation string
   * @param {object} variables - Mutation variables
   * @returns {Promise<any>} Mutation result
   */
  async mutate(mutation, variables = {}) {
    return this.request(mutation, variables);
  }
}

// Export singleton instance
export const graphqlClient = new GraphQLClientWrapper();

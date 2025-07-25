// Auto-generated TypeScript interfaces from ontology

// example - Example ontology for testing

// Version: 1.0.0

/** A person entity */
export interface Person {
  /** Full name of the person */
  name: string;
  /** Age of the person */
  age: number;
  /** Email address */
  email: string?;
  /** Current status */
  status: string;
}

/** A product entity */
export interface Product {
  /** Unique product identifier */
  id: string;
  /** Product name */
  name: string;
  /** Product price */
  price: number;
  /** Product category */
  category: string;
}

export type ExampleEntity = Person | Product;

/** Root interface that can represent any entity type */
export interface ExampleRoot {
  type: ExampleEntity;
  data: ExampleEntity;
}

// Utility types
export type ExampleEntityTypes = keyof typeof ExampleEntities;

export const ExampleEntities = {
  Person: 'Person',
  Product: 'Product',
} as const;

// Type guards
export function isPerson(obj: any): obj is Person {
  return obj && typeof obj === 'object' && 'type' in obj && obj.type === 'Person';
}

export function isProduct(obj: any): obj is Product {
  return obj && typeof obj === 'object' && 'type' in obj && obj.type === 'Product';
}

// Example usage:
// import { Person, Product } from './example_interfaces';
//
// const data: Person = {
//   // ... field values
// };
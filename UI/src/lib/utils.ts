import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Get currency symbol from currency code
 * @param currencyCode - ISO 4217 currency code (e.g., USD, EUR, GBP)
 * @returns Currency symbol (e.g., $, €, £)
 */
export function getCurrencySymbol(currencyCode: string = 'USD'): string {
  const currencySymbols: Record<string, string> = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'CNY': '¥',
    'INR': '₹',
    'AUD': 'A$',
    'CAD': 'C$',
    'CHF': 'Fr',
    'SEK': 'kr',
    'NOK': 'kr',
    'DKK': 'kr',
    'PLN': 'zł',
    'RUB': '₽',
    'BRL': 'R$',
    'ZAR': 'R',
    'MXN': 'Mex$',
    'KRW': '₩',
    'TRY': '₺',
    'NZD': 'NZ$',
    'SGD': 'S$',
    'HKD': 'HK$',
  };
  
  return currencySymbols[currencyCode.toUpperCase()] || currencyCode;
}

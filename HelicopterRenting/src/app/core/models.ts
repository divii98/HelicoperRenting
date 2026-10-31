export interface User {
  id: string;
  name: string;
  email: string;
}

export interface Resource {
  id: number;
  name: string;
  description: string;
  category: string;
  capacity: number;
  slot_minutes: number;
  open_time: string;
  close_time: string;
  price_cents: number;
  active: boolean;
}

export interface Slot {
  slotStart: string;
  slotEnd: string;
  capacity: number;
  booked: number;
  available: number;
}

export interface Availability {
  resource: Resource;
  slots: Slot[];
}

export interface Booking {
  id: number;
  resource_id: number;
  resource_name: string;
  user_id: string;
  unit_number: number;
  slot_start: string;
  slot_end: string;
  status: string;
  notes: string | null;
  created_at: string;
}

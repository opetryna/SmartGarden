#include <avr/sleep.h>

void setup() {
  UCSR0A = 0 << TXC0 | 0 << U2X0 | 0 << MPCM0;
  UCSR0B = 1 << RXCIE0 | 0 << TXCIE0 | 0 << UDRIE0 | 1 << RXEN0 | 1 << TXEN0 | 0 << UCSZ02 | 0 << TXB80;
  UCSR0C = 0 << UMSEL01 | 0 << UMSEL00 | 0 << UPM01 | 0 << UPM00 | 0 << USBS0 | 1 << UCSZ01 | 1 << UCSZ00 | 0 << UCPOL0;
  UBRR0 = F_CPU / 16 / 9600 - 1;
  asm("SEI");
}

void USART_print(char c) {
  while (0 == (UCSR0A & (1 << UDRE0)));
  UDR0 = c;
}

void USART_print(char* s) {
  while (*s) {
    USART_print(*s);
    ++s;
  }
}

void USART_print(int i) {
  char s[6];
  itoa(i, s, 10);
  USART_print(s);
}

ISR(USART_RX_vect) {
  char c = UDR0;
  if (c == 'r') {
    
    for (int i = 0; i < 6; i++) {
      int val = analogRead(i);
      
      USART_print(val);
      USART_print('\t');
    }
    
    USART_print("\r\n");
  }
}

void loop() {
  set_sleep_mode(SLEEP_MODE_IDLE);
  sleep_mode();
}
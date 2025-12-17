package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"

	"github.com/Bhavik2205/Research_Factory.git/internal/parser"
)



// MarketEvent struct (unchanged)
type MarketEvent struct {
	Source       string `json:"Source"`
	EventType    string `json:"EventType"`
	Symbol       string `json:"Symbol"`
	Exchange     string `json:"Exchange"`
	TimestampUTC uint64 `json:"TimestampUTC"`
	Payload      any    `json:"Payload"`
}

// --- NEW: DEFINE YOUR TARGET SYMBOL HERE ---
const targetSymbol = "SPY" // Change this to "HSBC" or whatever stock you want

func main() {
	log.SetOutput(os.Stderr)
	log.Println("[Go] Parser starting...")
    log.Printf("[Go] Filtering for SINGLE SYMBOL: %s", targetSymbol)

	stdoutWriter := bufio.NewWriter(os.Stdout)
	defer stdoutWriter.Flush()

	f, err := os.Open(`data\01302020.NASDAQ_ITCH50`)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()
	log.Println("[Go] ITCH file opened successfully.")

	sbr := parser.NewSoupBinReader(f)
	packetCount := 0
    messageCount := 0

	for { // Outer packet loop
		payload, err := sbr.NextPayload()
		packetCount++
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatalf("[Go] Framing error: %v", err)
		}
		if payload == nil {
			continue
		}
		if packetCount%100000 == 0 { // Changed to 100k
			log.Printf("[Go] Processing packet %d... (Found %d %s messages so far)", packetCount, messageCount, targetSymbol)
		}

		dec := parser.NewDecoder(bytes.NewReader(payload))

		for { // Inner message loop
			env, err := dec.Next()
			if err == io.EOF {
				break
			}
			if err != nil {
				log.Fatalf("[Go] Decode error: %v", err)
			}

			var eventType string
			var symbol string
			var timestamp uint64
			var msgPayload any

			switch m := env.Msg.(type) {
			
			case *parser.AddOrderNoMPIDAttribution:
                // --- NEW FILTER ---
                if m.Stock != targetSymbol { continue }
				eventType = "AddOrder"
				symbol = m.Stock
				timestamp = m.Header.Timestamp
				msgPayload = m

			case *parser.AddOrderWithMPIDAttribution:
                // --- NEW FILTER ---
                if m.Stock != targetSymbol { continue }
				eventType = "AddOrder"
				symbol = m.Stock
				timestamp = m.Header.Timestamp
				msgPayload = m

			case *parser.OrderExecuted:
				eventType = "OrderExecuted"
				symbol = "" // No symbol in this message
				timestamp = m.Header.Timestamp
				msgPayload = m

			case *parser.OrderExecutedWithPrice:
				eventType = "OrderExecutedWithPrice"
				symbol = "" // No symbol in this message
				timestamp = m.Header.Timestamp
				msgPayload = m

			default:
				continue
			}

			// Marshal and print
			marketEventJSON, err := json.Marshal(MarketEvent{
				Source:       "ITCH",
				EventType:    eventType,
				Symbol:       symbol,
				Exchange:     "NASDAQ",
				TimestampUTC: timestamp,
				Payload:      msgPayload,
			})
			if err != nil {
				log.Printf("[Go] JSON marshaling error: %v", err)
				continue
			}

            // We found a message we want!
            messageCount++
			fmt.Fprintln(stdoutWriter, string(marketEventJSON))
			err = stdoutWriter.Flush()
			if err != nil {
				log.Fatalf("[Go] Error flushing stdout: %v", err)
			}
		}
	}
	log.Printf("[Go] Parser finished file. Found a total of %d messages for %s.", messageCount, targetSymbol)
}







// package main

// import (
// 	"bufio" // <-- 1. IMPORT bufio
// 	"bytes"
// 	"encoding/json"
// 	"fmt"
// 	"io"
// 	"log"
// 	"os"

// 	"github.com/Bhavik2205/Research_Factory.git/internal/parser"
// )

// // ... (MarketEvent struct is unchanged) ...
// type MarketEvent struct {
// 	Source       string `json:"Source"`
// 	EventType    string `json:"EventType"`
// 	Symbol       string `json:"Symbol"`
// 	Exchange     string `json:"Exchange"`
// 	TimestampUTC uint64 `json:"TimestampUTC"`
// 	Payload      any    `json:"Payload"`
// }

// func main() {
// 	log.SetOutput(os.Stderr) // Logs to console
// 	log.Println("[Go] Parser starting...")

// 	// --- 2. CREATE A BUFFERED WRITER FOR STDOUT ---
// 	stdoutWriter := bufio.NewWriter(os.Stdout)
// 	// --- 3. DEFER A FINAL FLUSH ---
// 	defer stdoutWriter.Flush()

// 	f, err := os.Open(`data\01302020.NASDAQ_ITCH50`)
// 	if err != nil {
// 		log.Fatal(err)
// 	}
// 	defer f.Close()
// 	log.Println("[Go] ITCH file opened successfully.")

// 	sbr := parser.NewSoupBinReader(f)
// 	packetCount := 0

// 	for { // Outer packet loop
// 		payload, err := sbr.NextPayload()
// 		packetCount++
// 		if err == io.EOF {
// 			break
// 		}
// 		if err != nil {
// 			log.Fatalf("[Go] Framing error: %v", err)
// 		}
// 		if payload == nil {
// 			continue // heartbeat
// 		}
// 		if packetCount%1000 == 0 {
// 			log.Printf("[Go] Processing packet %d...", packetCount)
// 		}

// 		dec := parser.NewDecoder(bytes.NewReader(payload))

// 		for { // Inner message loop
// 			env, err := dec.Next()
// 			if err == io.EOF {
// 				break
// 			}
// 			if err != nil {
// 				log.Fatalf("[Go] Decode error: %v", err)
// 			}

// 			// (Switch statement is unchanged)
// 			var eventType string
// 			var symbol string
// 			var timestamp uint64
// 			var msgPayload any

// 			switch m := env.Msg.(type) {
// 			case *parser.AddOrderNoMPIDAttribution:
// 				eventType = "AddOrder"
// 				symbol = m.Stock
// 				timestamp = m.Header.Timestamp
// 				msgPayload = m
// 			case *parser.AddOrderWithMPIDAttribution:
// 				eventType = "AddOrder"
// 				symbol = m.Stock
// 				timestamp = m.Header.Timestamp
// 				msgPayload = m
// 			case *parser.OrderExecuted:
// 				eventType = "OrderExecuted"
// 				symbol = ""
// 				timestamp = m.Header.Timestamp
// 				msgPayload = m
// 			case *parser.OrderExecutedWithPrice:
// 				eventType = "OrderExecutedWithPrice"
// 				symbol = ""
// 				timestamp = m.Header.Timestamp
// 				msgPayload = m
// 			default:
// 				continue
// 			}

// 			// (JSON Marshal is unchanged)
// 			marketEventJSON, err := json.Marshal(MarketEvent{
// 				Source:       "ITCH",
// 				EventType:    eventType,
// 				Symbol:       symbol,
// 				Exchange:     "NASDAQ",
// 				TimestampUTC: timestamp,
// 				Payload:      msgPayload,
// 			})
// 			if err != nil {
// 				log.Printf("[Go] JSON marshaling error: %v", err)
// 				continue
// 			}

// 			// --- 4. THE FIX: Write to the buffered writer AND FLUSH ---
// 			// Change fmt.Println(...) to this:
// 			fmt.Fprintln(stdoutWriter, string(marketEventJSON)) // Write to the buffer
// 			err = stdoutWriter.Flush()                          // <-- FORCE THE BUFFER TO SEND
// 			if err != nil {
// 				log.Fatalf("[Go] Error flushing stdout: %v", err)
// 			}
// 			// --- END FIX ---
// 		}
// 	}
// 	log.Println("[Go] Parser finished file.")
// }

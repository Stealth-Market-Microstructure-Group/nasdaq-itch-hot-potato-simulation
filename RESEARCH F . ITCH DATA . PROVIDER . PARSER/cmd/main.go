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

// ================= SYMBOL FILTER LAYER =================

// OrderID -> Symbol
var orderSymbolMap = make(map[uint64]string)

// OrderID -> Remaining shares
var orderRemaining = make(map[uint64]uint32)

// Only process orders of this symbol
const targetSymbol = "SPY"

// Check if an order belongs to our target symbol
func isTargetOrder(orderID uint64) bool {
	sym, ok := orderSymbolMap[orderID]
	return ok && sym == targetSymbol
}

// ================= OUTPUT STRUCT =================

type MarketEvent struct {
	Source       string `json:"Source"`
	EventType    string `json:"EventType"`
	Symbol       string `json:"Symbol"`
	Exchange     string `json:"Exchange"`
	TimestampUTC uint64 `json:"TimestampUTC"`
	Payload      any    `json:"Payload"`
}

func main() {
	log.SetOutput(os.Stderr)
	log.Printf("[Go] Filtering ONLY symbol: %s", targetSymbol)

	// Output JSON filename
	outFile := "market_events.json"
	outF, err := os.Create(outFile)
	if err != nil {
		log.Fatal(err)
	}
	defer outF.Close()
	out := bufio.NewWriter(outF)
	defer out.Flush()

	// Input ITCH file
	inFile := `data\01302020.NASDAQ_ITCH50`
	f, err := os.Open(inFile)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	sbr := parser.NewSoupBinReader(f)

	for {
		payload, err := sbr.NextPayload()
		if err == io.EOF {
			break
		}
		if err != nil || payload == nil {
			continue
		}

		dec := parser.NewDecoder(bytes.NewReader(payload))

		for {
			env, err := dec.Next()
			if err == io.EOF {
				break
			}
			if err != nil {
				log.Fatal(err)
			}

			var (
				eventType string
				symbol    string
				ts        uint64
				msg       any
			)

			switch m := env.Msg.(type) {

			// ---------------- ADD ----------------

			case *parser.AddOrderNoMPIDAttribution, *parser.AddOrderWithMPIDAttribution:
				var orderID uint64
				var stock string
				var shares uint32
				var header parser.MessageHeader

				switch o := m.(type) {
				case *parser.AddOrderNoMPIDAttribution:
					orderID = o.OrderReferenceNumber
					stock = o.Stock
					shares = o.Shares
					header = o.Header
				case *parser.AddOrderWithMPIDAttribution:
					orderID = o.OrderReferenceNumber
					stock = o.Stock
					shares = o.Shares
					header = o.Header
				}

				orderSymbolMap[orderID] = stock
				orderRemaining[orderID] = shares

				if stock != targetSymbol {
					continue
				}

				eventType = "AddOrder"
				symbol = stock
				ts = header.Timestamp
				msg = m

			// ---------------- EXECUTE ----------------

			case *parser.OrderExecuted, *parser.OrderExecutedWithPrice:
				var orderID uint64
				var executed uint32
				var header parser.MessageHeader

				switch o := m.(type) {
				case *parser.OrderExecuted:
					orderID = o.OrderReferenceNumber
					executed = o.ExecutedShares
					header = o.Header
				case *parser.OrderExecutedWithPrice:
					orderID = o.OrderReferenceNumber
					executed = o.ExecutedShares
					header = o.Header
				}

				if !isTargetOrder(orderID) {
					continue
				}

				// safe reduce qty logic
				if remaining, ok := orderRemaining[orderID]; ok {
					if executed >= remaining {
						delete(orderRemaining, orderID)
						delete(orderSymbolMap, orderID)
					} else {
						orderRemaining[orderID] = remaining - executed
					}
				}

				eventType = "OrderExecuted"
				symbol = targetSymbol
				ts = header.Timestamp
				msg = m

			// ---------------- CANCEL ----------------

			case *parser.OrderCancel:
				orderID := m.OrderReferenceNumber
				canceled := m.CanceledShares

				if !isTargetOrder(orderID) {
					continue
				}

				// reduce order qty safely
				if remaining, ok := orderRemaining[orderID]; ok {
					if canceled >= remaining {
						delete(orderRemaining, orderID)
						delete(orderSymbolMap, orderID)
					} else {
						orderRemaining[orderID] = remaining - canceled
					}
				}

				eventType = "OrderCancel"
				symbol = targetSymbol
				ts = m.Header.Timestamp
				msg = m

			// ---------------- DELETE ----------------

			case *parser.OrderDelete:
				orderID := m.OrderReferenceNumber

				if !isTargetOrder(orderID) {
					continue
				}

				delete(orderRemaining, orderID)
				delete(orderSymbolMap, orderID)

				eventType = "OrderDelete"
				symbol = targetSymbol
				ts = m.Header.Timestamp
				msg = m

			// ---------------- REPLACE ----------------

			case *parser.OrderReplace:
				oldID := m.OriginalOrderRefNumber
				newID := m.NewOrderRefNumber

				if !isTargetOrder(oldID) {
					continue
				}

				// move state to new order
				orderSymbolMap[newID] = targetSymbol
				orderRemaining[newID] = m.Shares

				delete(orderSymbolMap, oldID)
				delete(orderRemaining, oldID)

				eventType = "OrderReplace"
				symbol = targetSymbol
				ts = m.Header.Timestamp
				msg = m

			default:
				continue
			}

			// Marshal JSON and write to output
			ev, _ := json.Marshal(MarketEvent{
				Source:       "ITCH",
				EventType:    eventType,
				Symbol:       symbol,
				Exchange:     "NASDAQ",
				TimestampUTC: ts,
				Payload:      msg,
			})
			fmt.Fprintln(out, string(ev))
		}
	}

	log.Printf("[Go] Finished writing events to %s", outFile)
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

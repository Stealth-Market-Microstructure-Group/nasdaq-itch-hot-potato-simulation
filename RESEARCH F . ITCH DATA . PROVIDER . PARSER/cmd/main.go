package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"io"
	"log"
	"os"

	"github.com/Bhavik2205/Research_Factory.git/internal/parser"
)

// ================= SYMBOL FILTER LAYER =================

var orderSymbolMap = make(map[uint64]string) // OrderID -> Symbol
var orderRemaining = make(map[uint64]uint32) // OrderID -> Remaining shares

const targetSymbol = "SPY"

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

	// ---------------- OUTPUT FILE ----------------
	outFile := "marketevents.jsonl"
	outF, err := os.Create(outFile)
	if err != nil {
		log.Fatal(err)
	}
	defer outF.Close()

	out := bufio.NewWriterSize(outF, 1<<20) // 1MB buffer

	// ---------------- INPUT FILE ----------------
	inFile := "../data/01302020.NASDAQ_ITCH50"
	f, err := os.Open(inFile)
	if err != nil {
		log.Fatal(err)
	}
	defer f.Close()

	sbr := parser.NewSoupBinReader(f)

	var processed uint64
	var written uint64

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

			processed++

			var (
				eventType string
				symbol    string
				ts        uint64
				msg       any
			)

			switch m := env.Msg.(type) {

			// ---------------- ADD ----------------
			case *parser.AddOrderNoMPIDAttribution:
				orderSymbolMap[m.OrderReferenceNumber] = m.Stock
				orderRemaining[m.OrderReferenceNumber] = m.Shares

				if m.Stock != targetSymbol {
					continue
				}

				eventType = "AddOrder"
				symbol = m.Stock
				ts = m.Header.Timestamp
				msg = m

			case *parser.AddOrderWithMPIDAttribution:
				orderSymbolMap[m.OrderReferenceNumber] = m.Stock
				orderRemaining[m.OrderReferenceNumber] = m.Shares

				if m.Stock != targetSymbol {
					continue
				}

				eventType = "AddOrder"
				symbol = m.Stock
				ts = m.Header.Timestamp
				msg = m

			// ---------------- EXECUTE ----------------
			case *parser.OrderExecuted:
				if !isTargetOrder(m.OrderReferenceNumber) {
					continue
				}

				if rem, ok := orderRemaining[m.OrderReferenceNumber]; ok {
					if m.ExecutedShares >= rem {
						delete(orderRemaining, m.OrderReferenceNumber)
						delete(orderSymbolMap, m.OrderReferenceNumber)
					} else {
						orderRemaining[m.OrderReferenceNumber] = rem - m.ExecutedShares
					}
				}

				eventType = "OrderExecuted"
				symbol = targetSymbol
				ts = m.Header.Timestamp
				msg = m

			case *parser.OrderExecutedWithPrice:
				if !isTargetOrder(m.OrderReferenceNumber) {
					continue
				}

				if rem, ok := orderRemaining[m.OrderReferenceNumber]; ok {
					if m.ExecutedShares >= rem {
						delete(orderRemaining, m.OrderReferenceNumber)
						delete(orderSymbolMap, m.OrderReferenceNumber)
					} else {
						orderRemaining[m.OrderReferenceNumber] = rem - m.ExecutedShares
					}
				}

				eventType = "OrderExecutedWithPrice"
				symbol = targetSymbol
				ts = m.Header.Timestamp
				msg = m

			// ---------------- CANCEL ----------------
			case *parser.OrderCancel:
				if !isTargetOrder(m.OrderReferenceNumber) {
					continue
				}

				if rem, ok := orderRemaining[m.OrderReferenceNumber]; ok {
					if m.CanceledShares >= rem {
						delete(orderRemaining, m.OrderReferenceNumber)
						delete(orderSymbolMap, m.OrderReferenceNumber)
					} else {
						orderRemaining[m.OrderReferenceNumber] = rem - m.CanceledShares
					}
				}

				eventType = "OrderCancel"
				symbol = targetSymbol
				ts = m.Header.Timestamp
				msg = m

			// ---------------- DELETE ----------------
			case *parser.OrderDelete:
				if !isTargetOrder(m.OrderReferenceNumber) {
					continue
				}

				delete(orderRemaining, m.OrderReferenceNumber)
				delete(orderSymbolMap, m.OrderReferenceNumber)

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

			ev, _ := json.Marshal(MarketEvent{
				Source:       "ITCH",
				EventType:    eventType,
				Symbol:       symbol,
				Exchange:     "NASDAQ",
				TimestampUTC: ts,
				Payload:      msg,
			})

			out.Write(ev)
			out.WriteByte('\n')
			written++

			// FORCE FLUSH + PROGRESS (CRITICAL)
			if written%10000 == 0 {
				out.Flush()
			}
			if processed%5_000_000 == 0 {
				log.Printf("[Go] processed=%d written=%d", processed, written)
			}
		}
	}

	out.Flush()
	log.Printf("[Go] DONE | processed=%d written=%d | file=%s", processed, written, outFile)
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

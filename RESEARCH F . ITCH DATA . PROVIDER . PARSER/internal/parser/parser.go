package parser

import (
	"bufio"
	"encoding/binary"
	"errors"
	"fmt"
	"io"
)

// SoupBinReader reads SoupBinTCP frames and returns ITCH payloads.
type SoupBinReader struct {
	r io.Reader
}

func NewSoupBinReader(r io.Reader) *SoupBinReader {
	return &SoupBinReader{r: r}
}

func (s *SoupBinReader) NextPayload() ([]byte, error) {
	var lenBuf [2]byte
	if _, err := io.ReadFull(s.r, lenBuf[:]); err != nil {
		return nil, err
	}
	n := binary.BigEndian.Uint16(lenBuf[:])
	if n == 0 {
		// Heartbeat (no payload)
		return nil, nil
	}
	buf := make([]byte, n)
	if _, err := io.ReadFull(s.r, buf); err != nil {
		return nil, err
	}
	return buf, nil
}

// Decoder parses Nasdaq TotalView-ITCH 5.0 messages from an io.Reader.
// It expects a raw ITCH stream (no SoupBinTCP/MoldUDP64 framing).
// All integer fields are big-endian per spec. Strings are ASCII right-padded with spaces.
//
// Spec reference (field positions/lengths) taken from the user's provided PDF.
// Key data-type notes:
// - Timestamp is 6 bytes: nanoseconds since midnight (u48).
// - Price(4) uses 4-byte integer with 4 implied decimals (divide by 10_000 for decimal).
// - Price(8) uses 8-byte integer with 8 implied decimals (divide by 10^8) — used in MWCB levels.
//
// Returned values are one of the concrete message structs defined in this package
// (e.g., *SystemEvent, *StockDirectory, *AddOrderNoMPIDAttribution, etc.).
// The Envelope struct includes the byte type so callers can type-switch safely.

type Envelope struct {
	Type byte
	Msg  any
}

var (
	ErrUnknownMessageType = errors.New("itch5: unknown message type")
)

const headerLen = 11 // MessageType(1) + StockLocate(2) + TrackingNumber(2) + Timestamp(6)

// Fixed byte lengths (total message length including the 1-byte type)
var msgLen = map[byte]int{
	'S': 12, // System Event
	'R': 39, // Stock Directory
	'H': 25, // Stock Trading Action
	'Y': 20, // Reg SHO Short Sale Price Test Restricted Indicator
	'L': 26, // Market Participant Position
	'V': 35, // MWCB Decline Level
	'W': 12, // MWCB Status
	'K': 28, // Quoting Period Update
	'J': 35, // LULD Auction Collar
	'h': 21, // Operational Halt
	'A': 36, // Add Order (No MPID)
	'F': 40, // Add Order with MPID
	'E': 31, // Order Executed
	'C': 36, // Order Executed with Price
	'X': 23, // Order Cancel
	'D': 19, // Order Delete
	'U': 35, // Order Replace
	'P': 44, // Trade (Non-Cross)
	'Q': 40, // Cross Trade
	'B': 19, // Broken Trade
	'I': 50, // Net Order Imbalance Indicator (NOII)
	'N': 20, // Retail Price Improvement Indicator
	'O': 48, // Direct Listing with Capital Raise Price Discovery
}

// compute max message size (including type)
var maxMsgLen int

func init() {
	for _, n := range msgLen {
		if n > maxMsgLen {
			maxMsgLen = n
		}
	}
}

// Decoder reads and decodes ITCH messages.
//
// It's safe for single-goroutine use. Create multiple decoders for concurrency.
// It reuses an internal buffer to avoid per-message allocations.

type Decoder struct {
	br  *bufio.Reader
	buf []byte // reusable buffer of size maxMsgLen-1 (we read type separately)
}

// NewDecoder wraps r in a buffered reader (64 KiB if not already buffered).
func NewDecoder(r io.Reader) *Decoder {
	if br, ok := r.(*bufio.Reader); ok {
		return &Decoder{br: br, buf: make([]byte, maxMsgLen-1)}
	}
	return &Decoder{br: bufio.NewReaderSize(r, 64*1024), buf: make([]byte, maxMsgLen-1)}
}

// Next reads the next message from the stream and returns an Envelope containing the type and the parsed struct.
// Returns io.EOF on clean end of stream.
func (d *Decoder) Next() (Envelope, error) {
	var env Envelope

	// Read message type (1 byte)
	t, err := d.br.ReadByte()
	if err != nil {
		return env, err
	}
	l := msgLen[t]
	if l == 0 {
		return env, fmt.Errorf("%w: 0x%02x", ErrUnknownMessageType, t)
	}

	// Read the remainder of the message (excluding the first byte already read)
	n := l - 1
	buf := d.buf[:n]
	if _, err := io.ReadFull(d.br, buf); err != nil {
		return env, err
	}

	// Parse header from the first 10 bytes (since type already consumed)
	if n < (headerLen - 1) { // headerLen includes type; we need at least 10 here
		return env, io.ErrUnexpectedEOF
	}
	h := MessageHeader{
		MessageType:    t,
		StockLocate:    beU16(buf[0:2]),
		TrackingNumber: beU16(buf[2:4]),
		Timestamp:      beU48(buf[4:10]),
	}
	p := buf[10:] // payload after header fields

	switch t {
	case 'S':
		if len(p) != 1 {
			return env, shortPayload("SystemEvent", 1, len(p))
		}
		m := &SystemEvent{Header: h, EventCode: p[0]}
		return Envelope{Type: t, Msg: m}, nil

	case 'R':
		if len(p) != 28 {
			return env, shortPayload("StockDirectory", 28, len(p))
		}
		m := &StockDirectory{Header: h}
		off := 0
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.MarketCategory = p[off]
		off++
		m.FinancialStatusIndicator = p[off]
		off++
		m.RoundLotSize = beU32(p[off : off+4])
		off += 4
		m.RoundLotsOnly = p[off]
		off++
		m.IssueClassification = p[off]
		off++
		m.IssueSubType = asciiTrim(p[off : off+2])
		off += 2
		m.Authenticity = p[off]
		off++
		m.ShortSaleThreshold = p[off]
		off++
		m.IPOFlag = p[off]
		off++
		m.LULDReferencePriceTier = p[off]
		off++
		m.ETPFlag = p[off]
		off++
		m.ETPLeverageFactor = beU32(p[off : off+4])
		off += 4
		m.InverseIndicator = p[off]
		return Envelope{Type: t, Msg: m}, nil

	case 'H':
		if len(p) != 14 {
			return env, shortPayload("StockTradingAction", 14, len(p))
		}
		m := &StockTradingAction{Header: h}
		off := 0
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.TradingState = p[off]
		off++
		m.Reserved = p[off]
		off++
		m.Reason = asciiTrim(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil

	case 'Y':
		if len(p) != 9 {
			return env, shortPayload("RegSHOShortSalePriceTestRestrictedIndicator", 9, len(p))
		}
		m := &RegSHOShortSalePriceTestRestrictedIndicator{Header: h}
		m.Stock = asciiTrim(p[0:8])
		m.RegSHOAction = p[8]
		return Envelope{Type: t, Msg: m}, nil

	case 'L':
		if len(p) != 15 {
			return env, shortPayload("MarketParticipantPosition", 15, len(p))
		}
		m := &MarketParticipantPosition{Header: h}
		off := 0
		m.MPID = asciiTrim(p[off : off+4])
		off += 4
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.PrimaryMarketMaker = p[off]
		off++
		m.MarketMakerMode = p[off]
		off++
		m.MarketParticipantState = p[off]
		return Envelope{Type: t, Msg: m}, nil

	case 'V':
		if len(p) != 24 {
			return env, shortPayload("MWCBDeclineLevel", 24, len(p))
		}
		m := &MWCBDeclineLevel{Header: h}
		m.Level1 = beU64(p[0:8])
		m.Level2 = beU64(p[8:16])
		m.Level3 = beU64(p[16:24])
		return Envelope{Type: t, Msg: m}, nil

	case 'W':
		if len(p) != 1 {
			return env, shortPayload("MWCBStatus", 1, len(p))
		}
		m := &MWCBStatus{Header: h, BreachedLevel: p[0]}
		return Envelope{Type: t, Msg: m}, nil

	case 'K':
		if len(p) != 17 {
			return env, shortPayload("QuotingPeriodUpdate", 17, len(p))
		}
		m := &QuotingPeriodUpdate{Header: h}
		off := 0
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.IPOQuotationReleaseTime = beU32(p[off : off+4])
		off += 4
		m.IPOQuotationReleaseQualifier = p[off]
		off++
		m.IPOPrice = beU32(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil

	case 'J':
		if len(p) != 24 {
			return env, shortPayload("LULDAuctionCollar", 24, len(p))
		}
		m := &LULDAuctionCollar{Header: h}
		off := 0
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.AuctionCollarReferencePrice = beU32(p[off : off+4])
		off += 4
		m.UpperAuctionCollarPrice = beU32(p[off : off+4])
		off += 4
		m.LowerAuctionCollarPrice = beU32(p[off : off+4])
		off += 4
		m.AuctionCollarExtension = beU32(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil

	case 'h':
		if len(p) != 10 {
			return env, shortPayload("OperationalHalt", 10, len(p))
		}
		m := &OperationalHalt{Header: h}
		off := 0
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.MarketCode = p[off]
		off++
		m.OperationalHaltAction = p[off]
		return Envelope{Type: t, Msg: m}, nil

	case 'A':
		if len(p) != 25 {
			return env, shortPayload("AddOrderNoMPIDAttribution", 25, len(p))
		}
		m := &AddOrderNoMPIDAttribution{Header: h}
		off := 0
		m.OrderReferenceNumber = beU64(p[off : off+8])
		off += 8
		m.BuySellIndicator = p[off]
		off++
		m.Shares = beU32(p[off : off+4])
		off += 4
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.Price = beU32(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil

	case 'F':
		if len(p) != 29 {
			return env, shortPayload("AddOrderWithMPIDAttribution", 29, len(p))
		}
		m := &AddOrderWithMPIDAttribution{Header: h}
		off := 0
		m.OrderReferenceNumber = beU64(p[off : off+8])
		off += 8
		m.BuySellIndicator = p[off]
		off++
		m.Shares = beU32(p[off : off+4])
		off += 4
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.Price = beU32(p[off : off+4])
		off += 4
		m.Attribution = asciiTrim(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil

	case 'E':
		if len(p) != 20 {
			return env, shortPayload("OrderExecuted", 20, len(p))
		}
		m := &OrderExecuted{Header: h}
		off := 0
		m.OrderReferenceNumber = beU64(p[off : off+8])
		off += 8
		m.ExecutedShares = beU32(p[off : off+4])
		off += 4
		m.MatchNumber = beU64(p[off : off+8])
		return Envelope{Type: t, Msg: m}, nil

	case 'C':
		if len(p) != 25 {
			return env, shortPayload("OrderExecutedWithPrice", 25, len(p))
		}
		m := &OrderExecutedWithPrice{Header: h}
		off := 0
		m.OrderReferenceNumber = beU64(p[off : off+8])
		off += 8
		m.ExecutedShares = beU32(p[off : off+4])
		off += 4
		m.MatchNumber = beU64(p[off : off+8])
		off += 8
		m.Printable = p[off]
		off++
		m.ExecutionPrice = beU32(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil

	case 'X':
		if len(p) != 12 {
			return env, shortPayload("OrderCancel", 12, len(p))
		}
		m := &OrderCancel{Header: h}
		off := 0
		m.OrderReferenceNumber = beU64(p[off : off+8])
		off += 8
		m.CanceledShares = beU32(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil

	case 'D':
		if len(p) != 8 {
			return env, shortPayload("OrderDelete", 8, len(p))
		}
		m := &OrderDelete{Header: h}
		m.OrderReferenceNumber = beU64(p[0:8])
		return Envelope{Type: t, Msg: m}, nil

	case 'U':
		if len(p) != 24 {
			return env, shortPayload("OrderReplace", 24, len(p))
		}
		m := &OrderReplace{Header: h}
		off := 0
		m.OriginalOrderRefNumber = beU64(p[off : off+8])
		off += 8
		m.NewOrderRefNumber = beU64(p[off : off+8])
		off += 8
		m.Shares = beU32(p[off : off+4])
		off += 4
		m.Price = beU32(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil

	case 'P':
		if len(p) != 33 {
			return env, shortPayload("TradeMessageNonCross", 33, len(p))
		}
		m := &TradeMessageNonCross{Header: h}
		off := 0
		m.OrderReferenceNumber = beU64(p[off : off+8])
		off += 8
		m.BuySellIndicator = p[off]
		off++
		m.Shares = beU32(p[off : off+4])
		off += 4
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.Price = beU32(p[off : off+4])
		off += 4
		m.MatchNumber = beU64(p[off : off+8])
		return Envelope{Type: t, Msg: m}, nil

	case 'Q':
		if len(p) != 29 {
			return env, shortPayload("CrossTradeMessage", 29, len(p))
		}
		m := &CrossTradeMessage{Header: h}
		off := 0
		m.Shares = beU64(p[off : off+8])
		off += 8
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.CrossPrice = beU32(p[off : off+4])
		off += 4
		m.MatchNumber = beU64(p[off : off+8])
		off += 8
		m.CrossType = p[off]
		return Envelope{Type: t, Msg: m}, nil

	case 'B':
		if len(p) != 8 {
			return env, shortPayload("BrokenTradeMessage", 8, len(p))
		}
		m := &BrokenTradeMessage{Header: h}
		m.MatchNumber = beU64(p[0:8])
		return Envelope{Type: t, Msg: m}, nil

	case 'I':
		if len(p) != 39 {
			return env, shortPayload("NetOrderImbalanceIndicator", 39, len(p))
		}
		m := &NetOrderImbalanceIndicator{Header: h}
		off := 0
		m.PairedShares = beU64(p[off : off+8])
		off += 8
		m.ImbalanceShares = beU64(p[off : off+8])
		off += 8
		m.ImbalanceDirection = p[off]
		off++
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.FarPrice = beU32(p[off : off+4])
		off += 4
		m.NearPrice = beU32(p[off : off+4])
		off += 4
		m.CurrentReferencePrice = beU32(p[off : off+4])
		off += 4
		m.CrossType = p[off]
		off++
		m.PriceVariationIndicator = p[off]
		return Envelope{Type: t, Msg: m}, nil

	case 'N':
		if len(p) != 9 {
			return env, shortPayload("RetailPriceImprovementIndicator", 9, len(p))
		}
		m := &RetailPriceImprovementIndicator{Header: h}
		m.Stock = asciiTrim(p[0:8])
		m.InterestFlag = p[8]
		return Envelope{Type: t, Msg: m}, nil

	case 'O':
		if len(p) != 37 {
			return env, shortPayload("DirectListingWithCapitalRaisePriceDiscovery", 37, len(p))
		}
		m := &DirectListingWithCapitalRaisePriceDiscovery{Header: h}
		off := 0
		m.Stock = asciiTrim(p[off : off+8])
		off += 8
		m.OpenEligibilityStatus = p[off]
		off++
		m.MinimumAllowablePrice = beU32(p[off : off+4])
		off += 4
		m.MaximumAllowablePrice = beU32(p[off : off+4])
		off += 4
		m.NearExecutionPrice = beU32(p[off : off+4])
		off += 4
		m.NearExecutionTime = beU64(p[off : off+8])
		off += 8
		m.LowerPriceRangeCollar = beU32(p[off : off+4])
		off += 4
		m.UpperPriceRangeCollar = beU32(p[off : off+4])
		return Envelope{Type: t, Msg: m}, nil
	}

	// Should never reach here due to earlier switch coverage
	return env, fmt.Errorf("%w: 0x%02x", ErrUnknownMessageType, t)
}

// Helpers

func beU16(b []byte) uint16 { return binary.BigEndian.Uint16(b) }
func beU32(b []byte) uint32 { return binary.BigEndian.Uint32(b) }
func beU64(b []byte) uint64 { return binary.BigEndian.Uint64(b) }

// beU48 decodes a 6-byte unsigned big-endian integer into a uint64
func beU48(b []byte) uint64 {
	_ = b[5]
	return (uint64(b[0]) << 40) | (uint64(b[1]) << 32) | (uint64(b[2]) << 24) | (uint64(b[3]) << 16) | (uint64(b[4]) << 8) | uint64(b[5])
}

// asciiTrim trims ASCII right-space padding from fixed-width ASCII fields.
func asciiTrim(b []byte) string {
	// trim only trailing spaces per spec
	i := len(b) - 1
	for i >= 0 && b[i] == ' ' {
		i--
	}
	return string(b[:i+1])
}

func shortPayload(name string, want, got int) error {
	return fmt.Errorf("itch5: %s payload length mismatch: want %d bytes, got %d", name, want, got)
}

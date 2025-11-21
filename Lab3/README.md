# MIT 6.102 (Spring 2025) Problem Set 4: Memory Scramble

This repository provides a TypeScript backend starter for the Memory Scramble assignment for [MIT 6.102](https://web.mit.edu/6.102/www/sp25/psets/ps4). The client UI is a single static file (`public/index.html`) that communicates with the backend over HTTP. The backend implements the game logic, board ADT, and concurrency semantics.

---

## Prerequisites

- [Node.js](https://nodejs.org/) (version 18+ recommended)
- [npm](https://www.npmjs.com/) (comes with Node.js)

---

## Project Structure

```
MIT-6.102-ps4/
├── boards/              # Sample board files
├── public/              # Static frontend (index.html)
├── src/                 # TypeScript backend source
│   ├── board.ts         # Board ADT implementation
│   ├── commands.ts      # Command glue functions
│   ├── server.ts        # Express HTTP server
│   └── simulation.ts    # Concurrency simulation
├── test/                # Unit tests
├── package.json         # npm configuration
├── tsconfig.json        # TypeScript config
├── Dockerfile           # (Optional) Docker support
├── docker-compose.yml   # (Optional) Docker Compose
└── README.md            # Project documentation
```

---

## Quick Start

```sh
# Install dependencies
npm install

# Compile and run server (example board)
npm start 0 boards/ab.txt

# Run tests
npm test

# Run simulation (concurrency stress test)
npm run simulation
```

---

## Notable Files

- `public/index.html`: Browser UI that calls the server endpoints
- `src/server.ts`: Express HTTP server (routes call the `commands` module)
- `src/commands.ts`: Glue functions (`look`, `flip`, `map`, `watch`) that only call `Board` methods
- `src/board.ts`: Board ADT implementation (representation, concurrency, operations)
- `src/simulation.ts`: Simulator for concurrent player actions
- `test/board.test.ts`: Unit tests for `Board`
- `boards/*.txt`: Sample board files

---

## Design Summary

- **Layering:**
  - HTTP server (`src/server.ts`) accepts requests and delegates to `src/commands.ts`.
  - `src/commands.ts` implements the string-based command API and **only** calls methods on the `Board` ADT (no direct server → board coupling).
  - `src/board.ts` implements the mutable, concurrency-aware Board ADT. It provides operations used by `commands` and implements change notification for `watch()`.

---

## Board ADT (Informal Specification)

### Abstraction Function
- The `Board` object represents a rectangular grid of `height x width` cells.
- Each cell either contains a card label (a `string`) or is empty (`null`).
- Each cell has a runtime `state` in {`none`, `down`, `up`, `my`}:
  - `none`: no card in the cell
  - `down`: card present but face-down (hidden)
  - `up`: card face-up and visible to all
  - `my`: card face-up and currently controlled by a single player

### Representation Invariant (RI)
- `height` and `width` are integers >= 0.
- `cards` is an array with length `height` and each `cards[r]` has length `width`.
- For every `r,c`, `cards[r][c]` is either `null` or a `string`.
- `state` and `owner` have dimensions `height x width`.
- If `state[r][c] === 'my'` then `owner[r][c]` is a non-empty `string`.
- If `state[r][c] !== 'my'` then `owner[r][c] === null`.

### Safety from Representation Exposure
- All internal arrays are private. Public methods return immutable snapshots (strings) or use defensive copies where needed. Callers never receive direct references to internal arrays or mutable objects.

### Key Public Methods
- `parseFromFile(filename: string): Promise<Board>`: Parse a board from a file.
- `toStringFor(playerId: string): string`: Get a snapshot for a player.
- `flip(playerId: string, row: number, col: number): Promise<void>`: Flip a card.
- `map(playerId: string, f: (card: string) => Promise<string>): Promise<void>`: Map card labels atomically.
- `watch(playerId: string): Promise<string>`: Wait for the next board change.

---

## Commands Module (`src/commands.ts`)

- `look(board, playerId)` — returns `board.toStringFor(playerId)`.
- `flip(board, playerId, row, column)` — calls `await board.flip(...)` then returns `board.toStringFor(playerId)`.
- `map(board, playerId, f)` — calls `await board.map(playerId, f)` then returns `board.toStringFor(playerId)`.
- `watch(board, playerId)` — calls `await board.watch(playerId)` and returns the snapshot.

---

## HTTP API (Server Endpoints)

- `GET /look/:playerId` — returns 200 with board snapshot.
- `GET /flip/:playerId/:row,:column` — tries to flip; on success returns 200 with snapshot; on failure returns 409 with an error message.
- `GET /replace/:playerId/:fromCard/:toCard` — applies `map` to replace all occurrences of `fromCard` with `toCard` and returns the snapshot.
- `GET /watch/:playerId` — long-poll that returns when the board changes.

### Example API Usage

```sh
# Look at the board as player 'alice'
curl http://localhost:8789/look/alice

# Flip a card at (0,1) as player 'bob'
curl http://localhost:8789/flip/bob/0,1

# Replace all 'A' cards with 'B' as player 'alice'
curl http://localhost:8789/replace/alice/A/B

# Watch for board changes as player 'bob'
curl http://localhost:8789/watch/bob
```

---

## Testing and Simulation

- Unit tests: `npm test` runs `tsc`, `eslint`, and the Mocha tests from `dist/test`. Current tests cover parsing, snapshot format, a matching flip scenario, and `map` behavior. The tests are in `test/board.test.ts`.
- Simulation: `npm run simulation` compiles and runs `src/simulation.ts`, which starts multiple concurrent player tasks (configured to 4 players, 100 moves each, random short delays). Use this to stress-test concurrency.

---

## Limitations and Notes

- The current implementation focuses on correctness of required semantics and on keeping the module separation enforced by the assignment. There are a few linter warnings (non-null assertions and `any` usage in a small polyfill) that can be cleaned up; these do not affect correctness.
- Additional tests are recommended to exercise concurrent flips, multiple waiting flips on the same cell, and `watch()` cancellation semantics.

---

## License

This project is for educational use as part of MIT 6.102. See assignment policies for details.


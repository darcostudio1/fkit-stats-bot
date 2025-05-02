import React, { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { DataGrid } from "@mui/x-data-grid";
import { Container, Typography, Box, TextField } from "@mui/material";

const supabase = createClient(
  process.env.REACT_APP_SUPABASE_URL,
  process.env.REACT_APP_SUPABASE_ANON_KEY
);

const columns = [
  { field: "discord_name", headerName: "Player", width: 180 },
  { field: "alliance", headerName: "Alliance", width: 120 },
  { field: "keep_name", headerName: "Keep Name", width: 160 },
  { field: "keep_level", headerName: "Keep Level", width: 110 },
  { field: "troop_level", headerName: "Troop Level", width: 120 },
  { field: "dragon_level", headerName: "Dragon", width: 100 },
  { field: "march_size", headerName: "March Size", width: 120 },
  { field: "house_level", headerName: "House Level", width: 120 },
  { field: "last_updated", headerName: "Last Updated", width: 150 },
];

function App() {
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function fetchStats() {
      let { data, error } = await supabase
        .from("player_stats")
        .select("id, discord_name, alliance, keep_name, keep_level, troop_level, dragon_level, march_size, house_level, last_updated")
        .order("last_updated", { ascending: false });
      if (error) return;
      // Only show the most recent for each (discord_id, keep_name)
      const seen = new Set();
      const filtered = data.filter(row => {
        const key = row.discord_name + "_" + row.keep_name;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      setRows(filtered.map(row => ({ ...row, id: row.id })));
    }
    fetchStats();
  }, []);

  const filteredRows = rows.filter(
    row =>
      Object.values(row)
        .join(" ")
        .toLowerCase()
        .includes(search.toLowerCase())
  );

  return (
    <Container maxWidth="xl" sx={{ mt: 6 }}>
      <Typography variant="h3" align="center" gutterBottom>
        FK!T Alliance Stats
      </Typography>
      <Box sx={{ mb: 2, display: "flex", justifyContent: "flex-end" }}>
        <TextField
          label="Search Players, Keeps, Stats..."
          variant="outlined"
          value={search}
          onChange={e => setSearch(e.target.value)}
          sx={{ width: 320 }}
        />
      </Box>
      <div style={{ height: 600, width: "100%" }}>
        <DataGrid
          rows={filteredRows}
          columns={columns}
          pageSize={20}
          rowsPerPageOptions={[20, 50, 100]}
          disableSelectionOnClick
          sx={{
            background: "#fff",
            borderRadius: 2,
            boxShadow: 2,
            fontSize: 16,
          }}
        />
      </div>
    </Container>
  );
}

export default App;

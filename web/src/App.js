import React, { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { DataGrid } from "@mui/x-data-grid";
import { Container, Typography, Box, TextField } from "@mui/material";

const supabase = createClient(
  process.env.REACT_APP_SUPABASE_URL,
  process.env.REACT_APP_SUPABASE_ANON_KEY
);

// Columns will be generated dynamically from data
const columnHeaderMap = {
  id: "ID",
  discord_name: "Player",
  alliance: "Branch", // Changed from 'Alliance' to 'Branch'
  keep_name: "Keep Name",
  keep_level: "Keep Level",
  troop_level: "Troop Level",
  dragon_level: "Dragon",
  march_size: "March Size",
  house_level: "House Level",
  last_updated: "Last Updated",
  // Add more mappings as needed
};


function App() {
  const [rows, setRows] = useState([]);
  const [search, setSearch] = useState("");
  const [branchFilter, setBranchFilter] = useState("");
  const [troopTypeFilter, setTroopTypeFilter] = useState("");
  const [troopLevelFilter, setTroopLevelFilter] = useState("");
  const [columns, setColumns] = useState([]);
  useEffect(() => {
    async function fetchStats() {
      let { data, error } = await supabase
        .from("player_stats")
        .select("*")
        .order("last_updated", { ascending: false });
      if (error) return;
      if (data && data.length > 0) {
        // Dynamically generate columns except for discord_id, id, and discord_name (Player)
        const keys = Object.keys(data[0]).filter(k => k !== "discord_id" && k !== "id" && k !== "discord_name");
        setColumns(
          keys.map(key => {
            let col = {
              field: key,
              headerName: columnHeaderMap[key] || key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
              width: 140,
            };
            if (key === "last_updated") {
              col.valueFormatter = (params) => {
                if (!params.value) return "";
                const d = new Date(params.value);
                return d.toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
              };
            }
            return col;
          })
        );
        setRows(data.map(row => ({ ...row, id: row.id })));
      } else {
        setColumns([]);
        setRows([]);
      }
    }
    fetchStats();
  }, []);

  // Get unique values for filters
  const branchOptions = Array.from(new Set(rows.map(row => row.alliance).filter(Boolean)));
  const troopTypeOptions = Array.from(new Set(rows.map(row => row.keep_name).filter(Boolean)));
  const troopLevelOptions = Array.from(new Set(rows.map(row => row.troop_level).filter(Boolean)));

  const filteredRows = rows.filter(row => {
    const matchesBranch = branchFilter ? row.alliance === branchFilter : true;
    const matchesTroopType = troopTypeFilter ? row.keep_name === troopTypeFilter : true;
    const matchesTroopLevel = troopLevelFilter ? row.troop_level === troopLevelFilter : true;
    const matchesSearch = Object.values(row)
      .join(" ")
      .toLowerCase()
      .includes(search.toLowerCase());
    return matchesBranch && matchesTroopType && matchesTroopLevel && matchesSearch;
  });

  return (
    <Container maxWidth="xl" sx={{ mt: 6 }}>
      <Typography variant="h3" align="center" gutterBottom>
        FK!T Alliance Stats
      </Typography>
      <Box sx={{ mb: 2, display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
        <TextField
          select
          label="Branch"
          value={branchFilter}
          onChange={e => setBranchFilter(e.target.value)}
          SelectProps={{ native: true }}
          sx={{ width: 180 }}
        >
          <option value="">All Branches</option>
          {branchOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </TextField>
        <TextField
          select
          label="Troop Type"
          value={troopTypeFilter}
          onChange={e => setTroopTypeFilter(e.target.value)}
          SelectProps={{ native: true }}
          sx={{ width: 180 }}
        >
          <option value="">All Troop Types</option>
          {troopTypeOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </TextField>
        <TextField
          select
          label="Troop Level"
          value={troopLevelFilter}
          onChange={e => setTroopLevelFilter(e.target.value)}
          SelectProps={{ native: true }}
          sx={{ width: 180 }}
        >
          <option value="">All Troop Levels</option>
          {troopLevelOptions.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </TextField>
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

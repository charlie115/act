"use client";

import { forwardRef, useImperativeHandle, useMemo, useState } from "react";

import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import SyncAltIcon from "@mui/icons-material/SyncAlt";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import ListItemButton from "@mui/material/ListItemButton";
import Stack from "@mui/material/Stack";

function OptionRow({ item, selected, onSelect, tradeSupportRequired }) {
  const disabled =
    item.disabled || (tradeSupportRequired && item.value !== "ALL" && !item.tradeSupport);

  return (
    <ListItemButton
      disabled={disabled}
      onClick={() => onSelect(item)}
      selected={selected}
      sx={{
        alignItems: "center",
        display: "flex",
        justifyContent: "space-between",
        gap: 2,
      }}
    >
      {item.target && item.origin ? (
        <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
          <span>{item.target.getLabel()}</span>
          <SyncAltIcon color="primary" fontSize="small" />
          <span>{item.origin.getLabel()}</span>
        </Stack>
      ) : (
        <span>{item.getLabel?.() || item.label || item.value}</span>
      )}

      <Stack direction="row" spacing={1}>
        {item.value !== "ALL" && item.tradeSupport ? (
          <Chip color="success" label="Trade Support" size="small" />
        ) : null}
        {item.secondaryIcon || null}
      </Stack>
    </ListItemButton>
  );
}

const BotMarketCodeCombinationSelector = forwardRef(function BotMarketCodeCombinationSelector(
  {
    buttonStyle,
    marketCodesRequired,
    onSelectItem,
    options = [],
    tradeSupportRequired,
    value,
  },
  ref
) {
  const [open, setOpen] = useState(false);

  useImperativeHandle(ref, () => ({
    open: () => setOpen(true),
    toggle: () => setOpen((current) => !current),
  }));

  const buttonLabel = useMemo(() => {
    if (value?.target && value?.origin) {
      return `${value.target.getLabel()} ↔ ${value.origin.getLabel()}`;
    }

    return value?.getLabel?.() || value?.label || "Select market code combination";
  }, [value]);

  function handleSelect(item) {
    if (item.disabled) {
      return;
    }

    onSelectItem?.(item);
    if (marketCodesRequired && item.value === "ALL") {
      return;
    }
    setOpen(false);
  }

  return (
    <Box sx={{ px: { xs: 0, md: 2 } }}>
      <Button
        endIcon={<ArrowDropDownIcon fontSize="small" />}
        onClick={() => setOpen(true)}
        sx={{
          fontSize: { xs: "0.72rem", md: "0.82rem" },
          justifyContent: "space-between",
          minWidth: 320,
          textTransform: "none",
          ...buttonStyle,
        }}
        variant="outlined"
      >
        {buttonLabel}
      </Button>
      <Dialog maxWidth="sm" onClose={() => setOpen(false)} open={open}>
        <DialogTitle sx={{ fontWeight: 700 }}>
          Select a market code combination
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {options.map((item) => (
            <OptionRow
              item={item}
              key={item.value}
              onSelect={handleSelect}
              selected={item.value === value?.value}
              tradeSupportRequired={tradeSupportRequired}
            />
          ))}
        </DialogContent>
      </Dialog>
    </Box>
  );
});

export default BotMarketCodeCombinationSelector;

"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import Avatar from "@mui/material/Avatar";
import Badge from "@mui/material/Badge";
import ConfirmationNumberIcon from "@mui/icons-material/ConfirmationNumber";
import DashboardIcon from "@mui/icons-material/Dashboard";
import AppRegistrationIcon from "@mui/icons-material/AppRegistration";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import LogoutIcon from "@mui/icons-material/Logout";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";

import { useAuth } from "../auth/AuthProvider";

export default function NextHeaderUserMenu() {
  const router = useRouter();
  const { authorizedListRequest, signOut, user } = useAuth();
  const [anchorEl, setAnchorEl] = useState(null);
  const [coupons, setCoupons] = useState([]);
  const [redemptions, setRedemptions] = useState([]);

  useEffect(() => {
    let active = true;

    async function loadCoupons() {
      try {
        const [nextCoupons, nextRedemptions] = await Promise.all([
          authorizedListRequest("/coupon/coupons/"),
          authorizedListRequest("/coupon/coupon-redemption/"),
        ]);

        if (!active) {
          return;
        }

        setCoupons(nextCoupons);
        setRedemptions(nextRedemptions);
      } catch {
        if (!active) {
          return;
        }

        setCoupons([]);
        setRedemptions([]);
      }
    }

    loadCoupons();

    return () => {
      active = false;
    };
  }, [authorizedListRequest]);

  const unusedCount = useMemo(() => {
    const redeemedCouponNames = new Set(redemptions.map((item) => item.coupon));
    return coupons.filter((coupon) => !redeemedCouponNames.has(coupon.name)).length;
  }, [coupons, redemptions]);

  const hasAffiliate = !!user?.affiliate;

  return (
    <>
      <IconButton id="next-user-menu-btn" onClick={(event) => setAnchorEl(event.currentTarget)} sx={{ p: 0 }}>
        <Avatar
          alt={user?.username || user?.email || "Account"}
          src={user?.profile?.picture}
          sx={{ bgcolor: user ? "primary.main" : null }}
        />
      </IconButton>
      <Menu
        anchorEl={anchorEl}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
        id="next-user-menu"
        onClose={() => setAnchorEl(null)}
        open={!!anchorEl}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
      >
        <MenuItem
          onClick={() => {
            router.push("/my-page");
            setAnchorEl(null);
          }}
        >
          <Avatar sx={{ width: 24, height: 24, mr: 1 }} />
          My Page
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            router.push("/coupon-dashboard");
            setAnchorEl(null);
          }}
        >
          <ListItemIcon>
            <Badge
              badgeContent={unusedCount}
              color="error"
              invisible={unusedCount === 0}
              overlap="rectangular"
            >
              <ConfirmationNumberIcon />
            </Badge>
          </ListItemIcon>
          <ListItemText>Coupon Dashboard</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={() => {
            router.push(hasAffiliate ? "/affiliate/dashboard" : "/request-affiliate");
            setAnchorEl(null);
          }}
        >
          <ListItemIcon>
            {hasAffiliate ? <DashboardIcon /> : <AppRegistrationIcon />}
          </ListItemIcon>
          <ListItemText>
            {hasAffiliate ? "Affiliate Dashboard" : "Apply for Affiliate Program"}
          </ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem
          onClick={async () => {
            await signOut();
            setAnchorEl(null);
            router.push("/");
          }}
        >
          <ListItemIcon>
            <LogoutIcon />
          </ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>
    </>
  );
}

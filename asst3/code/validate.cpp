#include "wireroute.h"
#include <algorithm>
#include <stdio.h>
#include <assert.h>

void validate_wire_t::print_wire() const {
  for (int i = 0; i < num_pts; i++) 
  {
    printf("[%u %u]", p[i].x, p[i].y);
    if (i != num_pts - 1) {
      printf(" -> ");
    } else {
      printf("\n");
    }
  }
}

validate_wire_t &validate_wire_t::cleanup(void) {
  /* Sort points by x-values */
  std::sort(p, p + num_pts, [](auto &a, auto &b) {
    return a.x < b.x || (a.x == b.x && a.y < b.y);});
  int i = 1;
  while (i < num_pts) {
    // Shift over duplicates
    if (p[i].x == p[i - 1].x && p[i].y == p[i - 1].y) {
      for (int j = i + 1; j < num_pts; j++) {
        p[j - 1] = p[j];
      }
      num_pts--;
    } else {
      i++;
    }
  }
  // Reorder for corner case
  if (num_pts == 4) {
    if (p[0].y == p[3].y) {
      std::swap(p[0], p[1]);
      std::swap(p[2], p[3]);
    } else if (p[0].y == p[2].y) {
      std::swap(p[1], p[2]);
    }
  } else if (num_pts == 3) {
    if (p[1].x == p[2].x && p[0].y != p[1].y) {
      std::swap(p[1], p[2]);
    } else if (p[0].x == p[1].x && p[1].y != p[2].y) {
      std::swap(p[0], p[1]);
    }
  }
  for (int i = 0; i < num_pts - 1; i++) {
    if (!(p[i].x == p[i + 1].x || p[i].y == p[i + 1].y)) [[unlikely]] {
      printf("cleanup: Created bad wire: ");
      print_wire();
      abort();
    }
  }
  return *this;
}

void wr_checker::validate() const {
  std::vector occ_computed(dim_y, std::vector<int>(dim_x));

  for (int wi = 0; wi < nwires; wi++) {
    const auto &w = wires[wi];
    validate_wire_t wire = w.to_validate_format().cleanup();

    const auto &pts = wire.p;
    // Fill occupancy matrix
    int cur_point = 0;
    do {
      int x = pts[cur_point].x;
      int y = pts[cur_point].y;
      int x_n = pts[cur_point + 1].x;
      int y_n = pts[cur_point + 1].y;
      int x_step = (x_n > x) ? 1 : (x_n < x) ? -1 : 0;
      int y_step = (y_n > y) ? 1 : (y_n < y) ? -1 : 0;
      while (x != x_n || y != y_n) {
        occ_computed[y][x]++;
        x += x_step;
        y += y_step;
      }
      // include last point if on last line segment
      if (++cur_point == wire.num_pts - 1) {
        occ_computed[y][x]++;
      }
      assert(x == x_n && y == y_n);
    } while (cur_point < wire.num_pts - 1);
  }
  int total = 0;
  for (int i = 0; i < dim_y; i++) {
    for (int j = 0; j < dim_x; j++) {
      if (occ_computed[i][j] != occupancies[i][j]) {
        if (total++ < COST_REPORT_DEPTH)
          printf("Occupancy Matrix: Values mismatch at (%d, %d)\n", j, i);
      }
    }
  }
  if (total > 0) {
    printf("Validate: %d total mismatches.\n", total);
  }
}

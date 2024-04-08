export default ({ from, to, interval }) => {
  if (from.toMillis() >= to.toMillis()) return [];

  const whiteSpaceData = [];
  const diff = to.diff(from, [interval.unit]).toObject();
  if (diff[interval.unit] > interval.quantity) {
    Array.from(
      {
        length: diff[interval.unit] / interval.quantity - interval.quantity,
      },
      (_1, i) => i + 1
    ).forEach((num) => {
      const time = from.plus({
        [interval.unit]: num * interval.quantity,
      });
      whiteSpaceData.push({ time: time.toMillis() / 1000 });
    });
  }

  return whiteSpaceData;
};
